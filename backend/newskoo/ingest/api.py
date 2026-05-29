"""API connectors implementing :class:`SourceConnector` for ``fetch_method=="api"``.

Dispatches on ``source.api_kind``:

* ``gdelt``   — GDELT 2.0 DOC API (free, no key, global, massive).
* ``newsapi`` — NewsAPI.org ``/v2/everything`` or ``/v2/top-headlines`` using
  ``settings.newsapi_key``; no-ops (logs a warning, yields nothing) when the key
  is empty so the pipeline stays healthy without credentials.

Each yields item dicts shaped for :func:`newskoo.ingest.producer.emit_raw`:
``{url, canonical_url, title, summary, published, authors, content_type}``.
The articles returned by these APIs are *metadata + url*; the body is fetched
later by the parser stage following the url, so items carry ``raw_text=None``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import httpx

from newskoo.core.config import get_settings
from newskoo.core.logging import get_logger
from newskoo.ingest.politeness import PolitenessEngine, domain_of

if TYPE_CHECKING:
    from newskoo.models.source import Source

log = get_logger(__name__)

GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"
NEWSAPI_BASE = "https://newsapi.org/v2"

# Default GDELT query when a source declares none — broad, recent, English-ish.
_DEFAULT_GDELT_QUERY = "news"
_DEFAULT_MAX_RECORDS = 75


def _source_options(source: Source) -> dict[str, Any]:
    """API-specific knobs live in ``source.politeness['api']`` (free-form jsonb)."""
    politeness = getattr(source, "politeness", None) or {}
    opts = politeness.get("api")
    return dict(opts) if isinstance(opts, dict) else {}


# ── GDELT ────────────────────────────────────────────────────────────────────
def _build_gdelt_params(source: Source) -> dict[str, str]:
    opts = _source_options(source)
    query = str(opts.get("query") or _DEFAULT_GDELT_QUERY)
    max_records = int(opts.get("max_records") or _DEFAULT_MAX_RECORDS)
    params: dict[str, str] = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": str(max(1, min(250, max_records))),
        "sort": str(opts.get("sort") or "DateDesc"),
    }
    timespan = opts.get("timespan")
    if timespan:
        params["timespan"] = str(timespan)
    return params


def normalize_gdelt(article: dict[str, Any]) -> dict[str, Any] | None:
    url = (article.get("url") or "").strip()
    if not url:
        return None
    return {
        "url": url,
        "canonical_url": None,
        "title": (article.get("title") or "").strip() or None,
        "published": article.get("seendate") or None,
        "authors": [],
        "content_type": "application/json",
        # Useful hints carried through headers for the parser/persist stages.
        "headers": {
            k: str(v)
            for k, v in {
                "x-gdelt-domain": article.get("domain"),
                "x-gdelt-language": article.get("language"),
                "x-gdelt-sourcecountry": article.get("sourcecountry"),
            }.items()
            if v
        },
    }


async def fetch_gdelt(
    source: Source, engine: PolitenessEngine
) -> AsyncIterator[dict[str, Any]]:
    if not get_settings().gdelt_enabled:
        log.info("api.gdelt_disabled", source_id=getattr(source, "id", None))
        return
    params = _build_gdelt_params(source)
    await engine.acquire(domain_of(GDELT_DOC_API), engine.default_rps)
    try:
        async with engine.client() as client:
            resp = await client.get(GDELT_DOC_API, params=params)
    except httpx.HTTPError as exc:
        log.warning("api.gdelt_failed", error=str(exc))
        return
    if resp.status_code >= 400:
        log.warning("api.gdelt_http_error", status=resp.status_code)
        return
    try:
        data = resp.json()
    except ValueError as exc:
        log.warning("api.gdelt_bad_json", error=str(exc))
        return
    for article in data.get("articles", []) or []:
        item = normalize_gdelt(article)
        if item is not None:
            item["http_status"] = resp.status_code
            yield item


# ── NewsAPI ────────────────────────────────────────────────────────────────
def _build_newsapi_request(source: Source) -> tuple[str, dict[str, str]]:
    opts = _source_options(source)
    endpoint = str(opts.get("endpoint") or "everything")
    if endpoint not in ("everything", "top-headlines"):
        endpoint = "everything"
    url = f"{NEWSAPI_BASE}/{endpoint}"
    params: dict[str, str] = {"pageSize": str(int(opts.get("page_size") or 100))}
    if endpoint == "everything":
        params["q"] = str(opts.get("q") or "news")
        params["sortBy"] = str(opts.get("sort_by") or "publishedAt")
        if opts.get("language"):
            params["language"] = str(opts["language"])
    else:  # top-headlines
        if opts.get("category"):
            params["category"] = str(opts["category"])
        if opts.get("country"):
            params["country"] = str(opts["country"])
        if opts.get("q"):
            params["q"] = str(opts["q"])
        if not opts.get("category") and not opts.get("country") and not opts.get("q"):
            # top-headlines requires at least one filter; default to US.
            params["country"] = "us"
    return url, params


def normalize_newsapi(article: dict[str, Any]) -> dict[str, Any] | None:
    url = (article.get("url") or "").strip()
    if not url:
        return None
    author = (article.get("author") or "").strip()
    return {
        "url": url,
        "canonical_url": None,
        "title": (article.get("title") or "").strip() or None,
        "summary": article.get("description") or None,
        # content from NewsAPI is truncated; keep as a hint only.
        "content": article.get("content") or None,
        "published": article.get("publishedAt") or None,
        "authors": [author] if author else [],
        "content_type": "application/json",
    }


async def fetch_newsapi(
    source: Source, engine: PolitenessEngine
) -> AsyncIterator[dict[str, Any]]:
    key = get_settings().newsapi_key
    if not key:
        log.warning("api.newsapi_no_key", source_id=getattr(source, "id", None))
        return
    url, params = _build_newsapi_request(source)
    await engine.acquire(domain_of(url), engine.default_rps)
    try:
        async with engine.client() as client:
            resp = await client.get(url, params=params, headers={"X-Api-Key": key})
    except httpx.HTTPError as exc:
        log.warning("api.newsapi_failed", error=str(exc))
        return
    if resp.status_code >= 400:
        log.warning("api.newsapi_http_error", status=resp.status_code)
        return
    try:
        data = resp.json()
    except ValueError as exc:
        log.warning("api.newsapi_bad_json", error=str(exc))
        return
    if data.get("status") != "ok":
        log.warning("api.newsapi_error", message=data.get("message"))
        return
    for article in data.get("articles", []) or []:
        item = normalize_newsapi(article)
        if item is not None:
            item["http_status"] = resp.status_code
            yield item


_DISPATCH = {
    "gdelt": fetch_gdelt,
    "newsapi": fetch_newsapi,
}


@dataclass
class ApiConnector:
    """Collector for ``fetch_method == "api"``; dispatches by ``api_kind``."""

    fetch_method: str = "api"
    engine: PolitenessEngine = field(default_factory=PolitenessEngine)

    async def fetch(self, source: Source) -> AsyncIterator[dict]:
        api_kind = (getattr(source, "api_kind", None) or "").lower()
        handler = _DISPATCH.get(api_kind)
        if handler is None:
            log.warning(
                "api.unknown_kind",
                api_kind=api_kind,
                source_id=getattr(source, "id", None),
            )
            return
        async for item in handler(source, self.engine):
            yield item
