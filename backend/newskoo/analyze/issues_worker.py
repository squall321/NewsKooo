"""Issues worker: periodic anomaly detection → ``issues.alerts``.

The "issues" stage. Unlike the analyzer, this is **pull-based**: on a fixed
cadence (``settings.issue_window_minutes``) it rebuilds the mention time-series
from PostgreSQL, recomputes velocity/z-score, detects spikes, and publishes an
:class:`IssueAlert` per spiking series to ``issues.alerts``. Reading from the DB
(rather than consuming ``analyze.results``) avoids racing the persistence stage.

Run until cancelled / SIGINT / SIGTERM, then shut down gracefully.
"""

from __future__ import annotations

import asyncio
import contextlib
import signal

from aiokafka import AIOKafkaProducer

from newskoo.analyze.issues import IssueDetector
from newskoo.core.config import get_settings
from newskoo.core.contracts import Topic
from newskoo.core.db import dispose_engine, session_scope
from newskoo.core.kafka import make_producer, publish
from newskoo.core.logging import configure_logging, get_logger

log = get_logger(__name__)


def _install_signal_handlers(stop: asyncio.Event) -> None:
    """Set the stop event on SIGINT/SIGTERM (best-effort; Windows lacks SIGTERM)."""
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, getattr(signal, "SIGTERM", None)):
        if sig is None:
            continue
        with contextlib.suppress(NotImplementedError, ValueError):
            loop.add_signal_handler(sig, stop.set)


async def run_once(producer: AIOKafkaProducer, detector: IssueDetector) -> int:
    """One detection cycle: rebuild → score → detect → publish. Returns alert count.

    Rebuild + score happen in one transaction; detection reuses the scored
    series in-memory so it sees a consistent snapshot.
    """
    async with session_scope() as session:
        await detector.rebuild_timeseries(session)
        scored = await detector.compute_anomalies(session)
        alerts = await detector.detect(session, series=scored)

    for alert in alerts:
        await publish(
            producer,
            Topic.ISSUES_ALERTS,
            alert,
            key=f"{alert.target_type}:{alert.target_id}",
        )
        log.info(
            "issues.alert_published",
            target_type=alert.target_type,
            target_id=alert.target_id,
            label=alert.label,
            score=alert.score,
        )
    return len(alerts)


async def run() -> None:
    """Run the periodic issue-detection loop until signalled/cancelled."""
    configure_logging()
    settings = get_settings()
    stop = asyncio.Event()
    _install_signal_handlers(stop)

    detector = IssueDetector()
    producer = await make_producer()
    interval_s = max(60.0, settings.issue_window_minutes * 60.0)
    log.info("issues.worker_started", interval_s=interval_s, threshold=detector.zscore_threshold)

    try:
        while not stop.is_set():
            try:
                await run_once(producer, detector)
            except Exception as exc:  # one bad cycle must not kill the loop
                log.error("issues.cycle_failed", error=str(exc), error_type=type(exc).__name__)
            # Sleep for the window, but wake early if asked to stop.
            with contextlib.suppress(asyncio.TimeoutError):
                await asyncio.wait_for(stop.wait(), timeout=interval_s)
    except asyncio.CancelledError:  # pragma: no cover - cancellation path
        log.info("issues.worker_cancelled")
    finally:
        log.info("issues.worker_stopping")
        with contextlib.suppress(Exception):
            await producer.stop()
        with contextlib.suppress(Exception):
            await dispose_engine()
        log.info("issues.worker_stopped")


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(run())
