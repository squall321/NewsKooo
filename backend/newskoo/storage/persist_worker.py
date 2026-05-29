"""Persist worker: ``parsed.articles`` → DB + ``dedup.events`` + ``analyze.requests``.

Consumer group that, for each :class:`ParsedArticle`:

1. upserts the article into PostgreSQL (idempotent on ``canonical_url`` with a
   ``content_hash`` revision check) via :func:`storage.persist.persist_parsed`;
2. scans recent articles for near-duplicates via
   :func:`cluster.dedup.find_near_duplicate` and publishes a :class:`DedupEvent`
   to ``dedup.events``;
3. requests downstream LLM/embedding analysis by publishing an
   :class:`AnalyzeRequest` (embedding + entities + keywords + topics + sentiment
   + summary) to ``analyze.requests``.

Offsets are committed only after a message is fully handled. Per-message
failures never crash the loop: the offending payload + error context is routed
to ``dead.letter``. At-least-once delivery is safe because the DB writes are
idempotent.
"""

from __future__ import annotations

from typing import Any

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from newskoo.cluster.dedup import find_near_duplicate
from newskoo.core.contracts import (
    AnalysisKind,
    AnalyzeRequest,
    DedupEvent,
    ParsedArticle,
    Topic,
)
from newskoo.core.db import session_scope
from newskoo.core.kafka import make_consumer, make_producer, publish
from newskoo.core.logging import get_logger
from newskoo.storage.persist import persist_parsed

log = get_logger(__name__)

_CONSUMER_GROUP = "persist"

# Default analysis battery requested for every freshly-persisted article.
_DEFAULT_KINDS: list[AnalysisKind] = [
    AnalysisKind.EMBEDDING,
    AnalysisKind.ENTITIES,
    AnalysisKind.KEYWORDS,
    AnalysisKind.TOPICS,
    AnalysisKind.SENTIMENT,
    AnalysisKind.SUMMARY,
]

# Window of recent articles compared during near-duplicate detection.
_DEDUP_WINDOW = 500


def _dead_letter_payload(raw_value: Any, error: Exception) -> dict[str, Any]:
    """Build a JSON-serializable dead-letter envelope with error context."""
    return {
        "stage": "persist",
        "topic": str(Topic.PARSED_ARTICLES),
        "error_type": type(error).__name__,
        "error": str(error),
        "original": raw_value,
    }


async def _handle_message(producer: AIOKafkaProducer, raw_value: Any) -> None:
    """Process one parsed-article message end to end.

    Persists the article, emits a :class:`DedupEvent`, and requests analysis.
    Any failure is converted into a ``dead.letter`` record so the consume loop
    can commit and move on; re-raises only if dead-lettering itself fails.
    """
    try:
        art = ParsedArticle.model_validate(raw_value)
        async with session_scope() as session:
            article_id, is_new = await persist_parsed(session, art)
            dup = await find_near_duplicate(
                session,
                art.simhash,
                art.canonical_url,
                window=_DEDUP_WINDOW,
            )
    except Exception as exc:  # any failure becomes a dead-letter, not a crash
        log.warning(
            "persist.message_failed",
            error=str(exc),
            error_type=type(exc).__name__,
        )
        await producer.send_and_wait(
            str(Topic.DEAD_LETTER), _dead_letter_payload(raw_value, exc)
        )
        return

    dedup_event = DedupEvent(
        article_id=article_id,
        canonical_url=art.canonical_url,
        simhash=int(art.simhash or 0),
        is_duplicate=dup.is_duplicate,
        event_id=None,
        near_duplicate_ids=dup.near_duplicate_ids,
    )
    await publish(producer, Topic.DEDUP_EVENTS, dedup_event, key=art.canonical_url)

    analyze_request = AnalyzeRequest(
        target_type="article",
        target_id=article_id,
        kinds=list(_DEFAULT_KINDS),
        language=art.language,
    )
    await publish(
        producer,
        Topic.ANALYZE_REQUESTS,
        analyze_request,
        key=str(article_id),
    )

    log.info(
        "persist.handled",
        article_id=article_id,
        is_new=is_new,
        is_duplicate=dup.is_duplicate,
        near_dups=len(dup.near_duplicate_ids),
    )


async def run() -> None:
    """Run the persist consumer loop until cancelled (wired by ``workers.run``).

    Commits offsets after each message is handled (published or dead-lettered),
    giving at-least-once delivery with idempotent upserts.
    """
    consumer: AIOKafkaConsumer = await make_consumer(
        Topic.PARSED_ARTICLES, group=_CONSUMER_GROUP
    )
    producer: AIOKafkaProducer = await make_producer()
    log.info("persist.worker_started", group=_CONSUMER_GROUP)
    try:
        async for msg in consumer:
            try:
                await _handle_message(producer, msg.value)
            except Exception as exc:  # keep the loop alive on broker hiccups
                log.error("persist.handle_unrecoverable", error=str(exc))
                continue
            await consumer.commit()
    finally:
        await consumer.stop()
        await producer.stop()
        log.info("persist.worker_stopped", group=_CONSUMER_GROUP)
