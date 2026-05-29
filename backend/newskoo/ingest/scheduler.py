"""Crawl scheduler: APScheduler ``AsyncIOScheduler`` driving per-source cadence.

Each enabled source is scheduled on an interval derived from its categories and
bot-sensitivity (fast-moving general/markets news polls often; niche/scientific
and bot-sensitive sources poll rarely). One *collection cycle* per source:

  1. resolve the connector class via ``CONNECTOR_REGISTRY`` + :mod:`importlib`,
  2. iterate ``connector.fetch(source)``,
  3. ``emit_raw`` every item to ``raw.documents``,
  4. record the crawl outcome into ``Source.health`` (best-effort, never fatal).

The scheduler holds no DB session itself; callers pass a producer + politeness
engine + concurrency semaphore so the whole worker shares one polite budget.
"""

from __future__ import annotations

import asyncio
import importlib
import time
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from newskoo.core.db import session_scope
from newskoo.core.logging import get_logger
from newskoo.ingest.politeness import PolitenessEngine
from newskoo.ingest.producer import _Producer, emit_raw
from newskoo.models.source import Source
from newskoo.sources.connectors import CONNECTOR_REGISTRY, SourceConnector

log = get_logger(__name__)

# Cadence (seconds) keyed by the most "live" category a source carries.
_FAST = {"markets", "finance", "economy", "business", "general", "breaking", "world"}
_MEDIUM = {"technology", "tech", "politics", "sports", "health", "energy"}
# Everything else (science, niche, long-tail) is slow.

_CADENCE_FAST_S = 5 * 60
_CADENCE_MEDIUM_S = 15 * 60
_CADENCE_SLOW_S = 60 * 60

# Bot-sensitivity multiplies the interval (be gentler with touchy sites).
_BOT_MULTIPLIER = {0: 1.0, 1: 1.5, 2: 3.0, 3: 6.0}


def cadence_for(source: Source) -> int:
    """Return the polling interval in seconds for ``source``."""
    cats = {c.lower() for c in (getattr(source, "categories", None) or [])}
    if cats & _FAST:
        base = _CADENCE_FAST_S
    elif cats & _MEDIUM:
        base = _CADENCE_MEDIUM_S
    else:
        base = _CADENCE_SLOW_S
    mult = _BOT_MULTIPLIER.get(int(getattr(source, "bot_sensitivity", 0) or 0), 1.0)
    return int(base * mult)


def resolve_connector(
    fetch_method: str, engine: PolitenessEngine | None = None
) -> SourceConnector:
    """Instantiate the connector registered for ``fetch_method``.

    Resolves the dotted ``module.ClassName`` path from ``CONNECTOR_REGISTRY`` via
    :mod:`importlib` and constructs it, sharing the politeness engine when the
    class accepts an ``engine`` argument.
    """
    dotted = CONNECTOR_REGISTRY.get(fetch_method)
    if not dotted:
        raise KeyError(f"no connector for fetch_method={fetch_method!r}")
    module_path, _, class_name = dotted.rpartition(".")
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    try:
        return cls(engine=engine) if engine is not None else cls()
    except TypeError:
        # Connector without an ``engine`` kwarg.
        return cls()


async def run_collection_cycle(
    source: Source,
    producer: _Producer,
    engine: PolitenessEngine,
    semaphore: asyncio.Semaphore | None = None,
) -> int:
    """Run one collection cycle for ``source``; return the count of emitted docs.

    Resolves the connector, streams ``fetch()`` and emits each item. Records the
    outcome into ``Source.health`` (separate short transaction). Never raises —
    a failing source must not kill the scheduler. An optional ``semaphore`` caps
    how many sources collect concurrently (``settings.crawler_max_concurrency``).
    """
    if semaphore is not None:
        async with semaphore:
            return await _run_collection_cycle(source, producer, engine)
    return await _run_collection_cycle(source, producer, engine)


async def _run_collection_cycle(
    source: Source, producer: _Producer, engine: PolitenessEngine
) -> int:
    started = time.monotonic()
    emitted = 0
    error: str | None = None
    try:
        connector = resolve_connector(source.fetch_method, engine)
        async for item in connector.fetch(source):
            try:
                await emit_raw(producer, source.id, item, source.fetch_method)
                emitted += 1
            except Exception as exc:  # one bad item must not abort the cycle
                log.warning(
                    "ingest.emit_failed",
                    source_id=source.id,
                    url=item.get("url"),
                    error=str(exc),
                )
    except Exception as exc:  # connector-level failure must not kill scheduler
        error = str(exc)
        log.warning("ingest.cycle_failed", source_id=source.id, error=error)

    latency_ms = (time.monotonic() - started) * 1000.0
    await _record_outcome(source.id, ok=error is None, latency_ms=latency_ms, error=error)
    log.info(
        "ingest.cycle_done",
        source_id=source.id,
        name=source.name,
        emitted=emitted,
        ok=error is None,
    )
    return emitted


async def _record_outcome(
    source_id: int, *, ok: bool, latency_ms: float, error: str | None
) -> None:
    """Persist the crawl outcome to source health; swallow DB errors."""
    from newskoo.sources.registry import record_health  # local import: avoid cycle

    try:
        async with session_scope() as session:
            await record_health(session, source_id, ok=ok, latency_ms=latency_ms, error=error)
    except Exception as exc:  # health recording is best-effort
        log.debug("ingest.health_record_failed", source_id=source_id, error=str(exc))


def build_scheduler(
    sources: Sequence[Source],
    producer: _Producer,
    engine: PolitenessEngine,
    *,
    semaphore: asyncio.Semaphore | None = None,
    scheduler: AsyncIOScheduler | None = None,
    jitter_s: int = 30,
    startup_stagger_s: int = 2,
) -> AsyncIOScheduler:
    """Build (but do not start) an ``AsyncIOScheduler`` with one job per source.

    Jobs run on a per-source interval (see :func:`cadence_for`). Initial runs are
    staggered by ``startup_stagger_s`` so all sources do not fire at once, and
    each run is offset by random ``jitter_s``. ``coalesce=True`` collapses missed
    runs; ``max_instances=1`` stops a slow source overlapping itself. The shared
    ``semaphore`` caps cross-source concurrency.
    """
    sched = scheduler or AsyncIOScheduler(timezone="UTC")
    now = datetime.now(UTC)
    scheduled = 0
    for source in sources:
        if not getattr(source, "enabled", True):
            continue
        if source.fetch_method not in CONNECTOR_REGISTRY:
            log.warning(
                "ingest.no_connector", source_id=source.id, method=source.fetch_method
            )
            continue
        interval = cadence_for(source)
        first_run = now + timedelta(seconds=scheduled * startup_stagger_s)
        sched.add_job(
            run_collection_cycle,
            trigger="interval",
            seconds=interval,
            args=[source, producer, engine, semaphore],
            id=f"src-{source.id}",
            name=f"collect:{source.name}",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=interval,
            jitter=jitter_s,
            next_run_time=first_run,
        )
        scheduled += 1
        log.debug("ingest.scheduled", source_id=source.id, interval_s=interval)
    log.info("ingest.scheduler_built", jobs=scheduled)
    return sched
