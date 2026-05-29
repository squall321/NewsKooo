"""Idempotent persistence of parsed articles into PostgreSQL.

The persist stage is the system of record's write path for the ``parsed.articles``
contract. It is **idempotent on ``canonical_url``** (the dedup key from
docs/DATA_MODEL.md) with a ``content_hash`` revision check:

* first sighting → insert a new :class:`Article` (``status='parsed'``);
* re-fetch with the **same** content hash → no-op (returns the existing id);
* re-fetch with a **changed** content hash → snapshot the prior title/body/hash
  into :class:`ArticleVersion`, then update the article in place.

A Redis :class:`~newskoo.core.redis.SeenSet` provides a cheap fast-path that
skips an obvious repeat without a DB round-trip; it is purely an optimisation —
correctness never depends on it (the DB lookup + unique ``canonical_url`` index
remain authoritative), so a missing/unavailable Redis is tolerated.
"""

from __future__ import annotations

from datetime import UTC, datetime

from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from newskoo.core.contracts import ParsedArticle
from newskoo.core.logging import get_logger
from newskoo.core.redis import SeenSet
from newskoo.models.article import Article, ArticleVersion
from newskoo.models.crawl import CrawlLog

log = get_logger(__name__)

# Module-level seen-set: a Redis SADD fast-path keyed by canonical_url. Lazily
# constructed so importing this module never requires a live Redis.
_seen: SeenSet | None = None


def _seen_set() -> SeenSet:
    global _seen
    if _seen is None:
        _seen = SeenSet("articles")
    return _seen


def _now() -> datetime:
    return datetime.now(UTC)


def _content_bytes(content_hash_hex: str) -> bytes:
    """Decode the contract's hex sha256 into the ``bytea`` column value."""
    return bytes.fromhex(content_hash_hex)


async def _existing_by_url(
    session: AsyncSession, canonical_url: str
) -> Article | None:
    res = await session.execute(
        select(Article).where(Article.canonical_url == canonical_url)
    )
    return res.scalar_one_or_none()


async def _maybe_seen_fast_path(canonical_url: str, content_hash_hex: str) -> bool:
    """Return True iff Redis says this (url, hash) pair was already persisted.

    Uses a single SADD: a member newly added is *not* a repeat (returns False);
    an already-present member is an obvious repeat (returns True). The member
    encodes the content hash so a revision (new hash) is never falsely skipped.
    Any Redis failure degrades to "not seen" so the DB path stays authoritative.
    """
    member = f"{canonical_url}\x00{content_hash_hex}"
    try:
        newly_added = await _seen_set().add_if_absent(member)
    except (RedisError, OSError):  # pragma: no cover - depends on live Redis
        return False
    return not newly_added


async def persist_parsed(
    session: AsyncSession, art: ParsedArticle
) -> tuple[int, bool]:
    """Upsert a :class:`ParsedArticle` keyed on ``canonical_url``.

    Returns ``(article_id, is_new)``. ``is_new`` is True only when a brand-new
    row was inserted. Flushes (to assign ids) but never commits — the caller's
    ``session_scope`` owns the transaction.
    """
    content_hash = _content_bytes(art.content_hash)
    fetched_at = art.fetched_at or _now()

    existing = await _existing_by_url(session, art.canonical_url)

    if existing is None:
        # Redis fast-path only helps once a row exists; for a brand-new URL we
        # still insert (the unique index guards against a concurrent racer).
        await _maybe_seen_fast_path(art.canonical_url, art.content_hash)
        article = Article(
            source_id=art.source_id,
            canonical_url=art.canonical_url,
            url=art.url,
            title=art.title,
            body=art.body,
            language=art.language,
            authors=list(art.authors),
            published_at=art.published_at,
            fetched_at=fetched_at,
            content_hash=content_hash,
            simhash=art.simhash,
            word_count=art.word_count,
            status="parsed",
        )
        session.add(article)
        await session.flush()
        log.info(
            "persist.inserted",
            article_id=article.id,
            canonical_url=art.canonical_url,
            source_id=art.source_id,
        )
        return int(article.id), True

    # Existing row: detect a revision via content hash.
    if existing.content_hash == content_hash:
        log.debug(
            "persist.unchanged",
            article_id=existing.id,
            canonical_url=art.canonical_url,
        )
        return int(existing.id), False

    # Content changed → snapshot the prior state, then update in place.
    session.add(
        ArticleVersion(
            article_id=existing.id,
            title=existing.title,
            body=existing.body,
            content_hash=existing.content_hash,
            fetched_at=existing.fetched_at,
        )
    )
    existing.title = art.title
    existing.body = art.body
    existing.content_hash = content_hash
    existing.simhash = art.simhash
    existing.word_count = art.word_count
    existing.fetched_at = fetched_at
    existing.status = "parsed"
    if art.language is not None:
        existing.language = art.language
    if art.published_at is not None:
        existing.published_at = art.published_at
    await session.flush()
    log.info(
        "persist.revised",
        article_id=existing.id,
        canonical_url=art.canonical_url,
    )
    return int(existing.id), False


async def write_crawl_log(
    session: AsyncSession,
    *,
    source_id: int | None,
    url: str,
    method: str,
    http_status: int | None = None,
    bytes_: int = 0,
    latency_ms: int = 0,
    ok: bool = True,
    error: str | None = None,
    fetched_at: datetime | None = None,
) -> CrawlLog:
    """Append one :class:`CrawlLog` row (per-fetch outcome for source health).

    Flushes but does not commit. Returns the persisted row.
    """
    entry = CrawlLog(
        source_id=source_id,
        url=url,
        method=method,
        http_status=http_status,
        bytes=bytes_,
        latency_ms=latency_ms,
        ok=ok,
        error=error,
        fetched_at=fetched_at or _now(),
    )
    session.add(entry)
    await session.flush()
    return entry
