"""Async CRUD + health tracking over the :class:`Source` registry.

Every function takes an :class:`~sqlalchemy.ext.asyncio.AsyncSession` so callers
control the transaction (use :func:`newskoo.core.db.session_scope`). The
functions flush but never commit, keeping them composable inside a larger unit
of work and trivially testable against a mocked session.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from newskoo.core.logging import get_logger
from newskoo.models.source import Source
from newskoo.sources.schemas import SourceCreate, SourceUpdate, politeness_for

log = get_logger(__name__)

# Health-history ring buffer size kept in ``Source.health["recent"]``.
_HEALTH_HISTORY = 20


def _apply_default_politeness(data: dict[str, Any]) -> dict[str, Any]:
    """Fill an empty ``politeness`` blob from the bot-sensitivity tier."""
    if not data.get("politeness"):
        tier = int(data.get("bot_sensitivity", 0) or 0)
        data["politeness"] = politeness_for(tier).model_dump()
    return data


async def create_source(session: AsyncSession, payload: SourceCreate) -> Source:
    """Insert a new source. Defaults politeness from ``bot_sensitivity``."""
    data = _apply_default_politeness(payload.model_dump())
    source = Source(**data)
    session.add(source)
    await session.flush()
    log.info("source.created", source_id=source.id, name=source.name)
    return source


async def get_source(session: AsyncSession, source_id: int) -> Source | None:
    """Fetch one source by primary key (or ``None``)."""
    return await session.get(Source, source_id)


async def get_by_feed_or_home(
    session: AsyncSession,
    *,
    feed_url: str | None = None,
    homepage_url: str | None = None,
) -> Source | None:
    """Look up a source by ``feed_url`` first, falling back to ``homepage_url``.

    This is the identity used for idempotent upserts.
    """
    if feed_url:
        res = await session.execute(select(Source).where(Source.feed_url == feed_url))
        found = res.scalar_one_or_none()
        if found is not None:
            return found
    if homepage_url:
        res = await session.execute(
            select(Source).where(Source.homepage_url == homepage_url)
        )
        return res.scalar_one_or_none()
    return None


async def list_sources(
    session: AsyncSession,
    *,
    enabled: bool | None = None,
    region: str | None = None,
    category: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[Source]:
    """List sources, optionally filtered by enabled/region/category."""
    stmt = select(Source).order_by(Source.id)
    if enabled is not None:
        stmt = stmt.where(Source.enabled.is_(enabled))
    if region is not None:
        stmt = stmt.where(Source.region == region)
    if category is not None:
        stmt = stmt.where(Source.categories.any(category))
    if offset:
        stmt = stmt.offset(offset)
    if limit is not None:
        stmt = stmt.limit(limit)
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def update_source(
    session: AsyncSession, source_id: int, payload: SourceUpdate
) -> Source | None:
    """Apply a partial update; only fields explicitly set are changed."""
    source = await session.get(Source, source_id)
    if source is None:
        return None
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(source, key, value)
    await session.flush()
    log.info("source.updated", source_id=source_id, fields=sorted(changes))
    return source


async def set_enabled(
    session: AsyncSession, source_id: int, enabled: bool
) -> Source | None:
    """Enable/disable a source."""
    source = await session.get(Source, source_id)
    if source is None:
        return None
    source.enabled = enabled
    await session.flush()
    log.info("source.enabled" if enabled else "source.disabled", source_id=source_id)
    return source


async def record_health(
    session: AsyncSession,
    source_id: int,
    ok: bool,
    latency_ms: float,
    error: str | None = None,
) -> Source | None:
    """Merge a fetch outcome into ``Source.health`` jsonb.

    Maintains running counters, a smoothed error rate, last latency, and a small
    ring buffer of recent outcomes for quick health inspection.
    """
    source = await session.get(Source, source_id)
    if source is None:
        return None

    health: dict[str, Any] = dict(source.health or {})
    now = datetime.now(UTC).isoformat()

    total = int(health.get("total", 0)) + 1
    fails = int(health.get("fails", 0)) + (0 if ok else 1)
    health["total"] = total
    health["fails"] = fails
    health["error_rate"] = round(fails / total, 4)
    health["last_latency_ms"] = round(float(latency_ms), 2)
    health["last_checked_at"] = now
    if ok:
        health["last_ok_at"] = now
        health.pop("last_error", None)
    else:
        health["last_error"] = error
        health["last_error_at"] = now

    recent: list[dict[str, Any]] = list(health.get("recent", []))
    recent.append({"at": now, "ok": ok, "latency_ms": round(float(latency_ms), 2)})
    health["recent"] = recent[-_HEALTH_HISTORY:]

    source.health = health
    await session.flush()
    return source


async def upsert_source(session: AsyncSession, payload: SourceCreate) -> Source:
    """Idempotently create-or-update a source keyed on feed_url else homepage_url.

    On match, mutable descriptive fields are refreshed (name, categories,
    languages, region, bot_sensitivity, …) while operational state (``enabled``,
    ``health``) is preserved.
    """
    existing = await get_by_feed_or_home(
        session, feed_url=payload.feed_url, homepage_url=payload.homepage_url
    )
    if existing is None:
        return await create_source(session, payload)

    data = _apply_default_politeness(payload.model_dump())
    # Preserve operational state of the existing row.
    data.pop("enabled", None)
    for key, value in data.items():
        setattr(existing, key, value)
    await session.flush()
    log.info("source.upserted", source_id=existing.id, name=existing.name)
    return existing
