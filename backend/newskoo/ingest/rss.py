"""RSS/Atom feed collector implementing :class:`SourceConnector`.

Fetches a source's ``feed_url`` with :mod:`httpx` (through the
:class:`~newskoo.ingest.politeness.PolitenessEngine`), parses it with
:mod:`feedparser`, and yields normalized item dicts:

    {url, canonical_url, title, summary, content (raw_html), published, authors,
     http_status, content_type, headers}

Conditional GET (ETag / Last-Modified) is supported via an in-memory per-feed
cache so re-polls are cheap and polite; HTTP/transport errors degrade to an
empty stream (logged), never raising into the scheduler.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import feedparser
import httpx

from newskoo.core.logging import get_logger
from newskoo.ingest.politeness import PolitenessEngine, domain_of

if TYPE_CHECKING:
    from newskoo.models.source import Source

log = get_logger(__name__)


def _rps_for(source: Source, engine: PolitenessEngine) -> float:
    """Resolve requests/sec for a source from its politeness blob, else default."""
    politeness = getattr(source, "politeness", None) or {}
    rps = politeness.get("rps")
    if isinstance(rps, (int, float)) and rps > 0:
        return float(rps)
    return engine.default_rps or 0.5


def _authors_of(entry: Any) -> list[str]:
    out: list[str] = []
    detail = entry.get("authors") or []
    for a in detail:
        name = (a.get("name") or "").strip() if isinstance(a, dict) else str(a).strip()
        if name and name not in out:
            out.append(name)
    single = (entry.get("author") or "").strip()
    if single and single not in out:
        out.append(single)
    return out


def _content_of(entry: Any) -> str | None:
    """Pick the richest content payload from a feed entry."""
    content = entry.get("content")
    if content:
        # feedparser yields a list of {value, type, ...}; take the longest value.
        values = [c.get("value", "") for c in content if isinstance(c, dict)]
        values = [v for v in values if v]
        if values:
            return max(values, key=len)
    return entry.get("summary") or None


def _published_of(entry: Any) -> str | None:
    return entry.get("published") or entry.get("updated") or None


def normalize_entry(entry: Any) -> dict[str, Any] | None:
    """Map a feedparser entry to a raw item dict, or ``None`` if it has no link."""
    url = (entry.get("link") or "").strip()
    if not url:
        return None
    # RSS rarely exposes a canonical link distinct from <link>; carry id if URL-ish.
    guid = (entry.get("id") or "").strip()
    canonical = guid if guid.startswith(("http://", "https://")) else None
    return {
        "url": url,
        "canonical_url": canonical,
        "title": (entry.get("title") or "").strip() or None,
        "summary": entry.get("summary") or None,
        "content": _content_of(entry),
        "published": _published_of(entry),
        "authors": _authors_of(entry),
    }


@dataclass(slots=True)
class _FeedCacheEntry:
    etag: str | None = None
    last_modified: str | None = None


@dataclass
class RssConnector:
    """Collector for ``fetch_method == "rss"`` sources."""

    fetch_method: str = "rss"
    engine: PolitenessEngine = field(default_factory=PolitenessEngine)
    _cache: dict[str, _FeedCacheEntry] = field(default_factory=dict, repr=False)

    async def fetch(self, source: Source) -> AsyncIterator[dict]:
        feed_url = getattr(source, "feed_url", None)
        if not feed_url:
            log.warning("rss.no_feed_url", source_id=getattr(source, "id", None))
            return
        domain = domain_of(feed_url)
        ua = self.engine.next_user_agent()

        if not await self.engine.can_fetch(feed_url, ua):
            log.info("rss.robots_disallow", url=feed_url)
            return

        await self.engine.acquire(domain, _rps_for(source, self.engine))

        cache = self._cache.setdefault(feed_url, _FeedCacheEntry())
        req_headers: dict[str, str] = {}
        if cache.etag:
            req_headers["If-None-Match"] = cache.etag
        if cache.last_modified:
            req_headers["If-Modified-Since"] = cache.last_modified

        try:
            async with self.engine.client(ua=ua) as client:
                resp = await client.get(feed_url, headers=req_headers)
        except httpx.HTTPError as exc:
            log.warning("rss.fetch_failed", url=feed_url, error=str(exc))
            return

        if resp.status_code == 304:
            log.debug("rss.not_modified", url=feed_url)
            return
        if resp.status_code >= 400:
            log.warning("rss.http_error", url=feed_url, status=resp.status_code)
            return

        # Persist validators for the next conditional GET.
        cache.etag = resp.headers.get("ETag", cache.etag)
        cache.last_modified = resp.headers.get("Last-Modified", cache.last_modified)
        content_type = resp.headers.get("content-type", "").split(";")[0].strip() or None

        parsed = feedparser.parse(resp.content)
        if parsed.bozo and not parsed.entries:
            log.warning(
                "rss.parse_bozo", url=feed_url, error=str(getattr(parsed, "bozo_exception", ""))
            )
            return

        for entry in parsed.entries:
            item = normalize_entry(entry)
            if item is None:
                continue
            item["http_status"] = resp.status_code
            item["content_type"] = content_type
            yield item
