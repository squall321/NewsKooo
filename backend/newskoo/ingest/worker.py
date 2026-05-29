"""Ingestion worker entrypoint.

``run()`` is the long-lived ingestion process (wired into
``newskoo.workers.run`` by the orchestrator — do **not** edit that file here):

  1. configure logging,
  2. load enabled sources from PostgreSQL,
  3. start a shared Kafka producer + a :class:`PolitenessEngine` + an
     :class:`asyncio.Semaphore` capping concurrent collections,
  4. build & start an APScheduler ``AsyncIOScheduler`` with one job per source,
  5. run until cancelled / SIGINT / SIGTERM, then shut down gracefully.

Launch (after the orchestrator wires the dispatch):
    ``python -m newskoo.workers.run scheduler``
or directly for local dev:
    ``python -c "import asyncio; from newskoo.ingest.worker import run; asyncio.run(run())"``
"""

from __future__ import annotations

import asyncio
import contextlib
import signal

from newskoo.core.config import get_settings
from newskoo.core.db import dispose_engine, session_scope
from newskoo.core.kafka import make_producer
from newskoo.core.logging import configure_logging, get_logger
from newskoo.ingest.politeness import PolitenessEngine
from newskoo.ingest.scheduler import build_scheduler
from newskoo.models.source import Source
from newskoo.sources.registry import list_sources

log = get_logger(__name__)


async def _load_enabled_sources() -> list[Source]:
    async with session_scope() as session:
        return await list_sources(session, enabled=True)


def _install_signal_handlers(stop: asyncio.Event) -> None:
    """Set the stop event on SIGINT/SIGTERM (best-effort; Windows lacks SIGTERM)."""
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, getattr(signal, "SIGTERM", None)):
        if sig is None:
            continue
        with contextlib.suppress(NotImplementedError, ValueError):
            loop.add_signal_handler(sig, stop.set)


async def run() -> None:
    """Run the ingestion scheduler forever (until signalled/cancelled)."""
    configure_logging()
    settings = get_settings()
    stop = asyncio.Event()
    _install_signal_handlers(stop)

    sources = await _load_enabled_sources()
    log.info("ingest.worker_start", sources=len(sources))

    engine = PolitenessEngine()
    semaphore = asyncio.Semaphore(max(1, settings.crawler_max_concurrency))
    producer = await make_producer()
    scheduler = build_scheduler(sources, producer, engine, semaphore=semaphore)

    scheduler.start()
    log.info("ingest.worker_running", jobs=len(scheduler.get_jobs()))
    try:
        await stop.wait()
    except asyncio.CancelledError:  # pragma: no cover - cancellation path
        log.info("ingest.worker_cancelled")
    finally:
        log.info("ingest.worker_stopping")
        with contextlib.suppress(Exception):
            scheduler.shutdown(wait=False)
        with contextlib.suppress(Exception):
            await producer.stop()
        with contextlib.suppress(Exception):
            await dispose_engine()
        log.info("ingest.worker_stopped")


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(run())
