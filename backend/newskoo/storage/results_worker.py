"""Results worker: ``analyze.results`` → DB (+ clustering side effects).

Consumer group that persists each :class:`AnalyzeResult` via
:func:`storage.results.persist_analysis` inside a transaction. The persist call
records the :class:`Analysis` audit row and applies kind-specific projections
(embedding → clustering, entities/keywords/topics → catalog + link upserts) and
advances ``articles.status`` to ``'analyzed'``.

Offsets are committed only after a message is fully handled. Per-message
failures are routed to ``dead.letter`` rather than crashing the loop;
at-least-once redelivery is safe because all writes are idempotent upserts.
"""

from __future__ import annotations

from typing import Any

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from newskoo.core.contracts import AnalyzeResult, Topic
from newskoo.core.db import session_scope
from newskoo.core.kafka import make_consumer, make_producer
from newskoo.core.logging import get_logger
from newskoo.storage.results import persist_analysis

log = get_logger(__name__)

_CONSUMER_GROUP = "results"


def _dead_letter_payload(raw_value: Any, error: Exception) -> dict[str, Any]:
    """Build a JSON-serializable dead-letter envelope with error context."""
    return {
        "stage": "results",
        "topic": str(Topic.ANALYZE_RESULTS),
        "error_type": type(error).__name__,
        "error": str(error),
        "original": raw_value,
    }


async def _handle_message(producer: AIOKafkaProducer, raw_value: Any) -> None:
    """Persist one analysis result; dead-letter on failure.

    Re-raises only if dead-lettering itself fails so the loop won't commit past
    an unhandled message.
    """
    try:
        res = AnalyzeResult.model_validate(raw_value)
        async with session_scope() as session:
            await persist_analysis(session, res)
    except Exception as exc:  # any failure becomes a dead-letter, not a crash
        log.warning(
            "results.message_failed",
            error=str(exc),
            error_type=type(exc).__name__,
        )
        await producer.send_and_wait(
            str(Topic.DEAD_LETTER), _dead_letter_payload(raw_value, exc)
        )
        return

    log.info(
        "results.handled",
        target_type=res.target_type,
        target_id=res.target_id,
        kind=str(res.kind),
    )


async def run() -> None:
    """Run the results consumer loop until cancelled (wired by ``workers.run``).

    Commits offsets after each message is handled (persisted or dead-lettered).
    """
    consumer: AIOKafkaConsumer = await make_consumer(
        Topic.ANALYZE_RESULTS, group=_CONSUMER_GROUP
    )
    producer: AIOKafkaProducer = await make_producer()
    log.info("results.worker_started", group=_CONSUMER_GROUP)
    try:
        async for msg in consumer:
            try:
                await _handle_message(producer, msg.value)
            except Exception as exc:  # keep the loop alive on broker hiccups
                log.error("results.handle_unrecoverable", error=str(exc))
                continue
            await consumer.commit()
    finally:
        await consumer.stop()
        await producer.stop()
        log.info("results.worker_stopped", group=_CONSUMER_GROUP)
