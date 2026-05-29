"""Analyzer worker: ``analyze.requests`` → ``analyze.results``.

Consumer group ("analyzer" stage) that, for each :class:`AnalyzeRequest`:

1. loads the target article's title/body/language from PostgreSQL by
   ``target_id`` (events are not yet supported and are dead-lettered);
2. runs each requested :class:`AnalysisKind` — LLM extraction via
   :func:`newskoo.analyze.extractors.analyze`, or an embedding via
   :func:`newskoo.analyze.embeddings.embed_text` for ``EMBEDDING``;
3. publishes one :class:`AnalyzeResult` per kind to ``analyze.results``
   (the embedding goes in ``AnalyzeResult.embedding`` for ``EMBEDDING``).

Offsets are committed only after a message is fully handled. Per-message
failures never crash the loop: the offending request plus error context is
routed to ``dead.letter``.
"""

from __future__ import annotations

from typing import Any

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from sqlalchemy import select

from newskoo.analyze.embeddings import embed_text
from newskoo.analyze.extractors import analyze
from newskoo.core.config import get_settings
from newskoo.core.contracts import AnalysisKind, AnalyzeRequest, AnalyzeResult, Topic
from newskoo.core.db import session_scope
from newskoo.core.kafka import make_consumer, make_producer, publish
from newskoo.core.logging import get_logger
from newskoo.models.article import Article

log = get_logger(__name__)

_CONSUMER_GROUP = "analyzer"

# Kinds the analyze stage implements (TRANSLATION is deferred).
_LLM_KINDS = frozenset(
    {
        AnalysisKind.ENTITIES,
        AnalysisKind.KEYWORDS,
        AnalysisKind.TOPICS,
        AnalysisKind.SENTIMENT,
        AnalysisKind.SUMMARY,
    }
)


class TargetText:
    """Resolved text for an analysis target."""

    __slots__ = ("body", "language", "title")

    def __init__(self, *, title: str | None, body: str, language: str | None) -> None:
        self.title = title
        self.body = body
        self.language = language


async def _load_target_text(target_type: str, target_id: int) -> TargetText:
    """Fetch title/body/language for the target from the DB.

    Only ``article`` targets are supported today; events would aggregate member
    article text and are out of scope for this stage.
    """
    if target_type != "article":
        raise ValueError(f"Unsupported analyze target_type: {target_type!r} (expected 'article')")
    async with session_scope() as session:
        row = (
            await session.execute(
                select(Article.title, Article.body, Article.language).where(
                    Article.id == target_id
                )
            )
        ).first()
    if row is None:
        raise LookupError(f"Article {target_id} not found for analysis")
    title, body, language = row
    return TargetText(title=title, body=body or "", language=language)


def _result_text(text: TargetText) -> str:
    """Combine title + body into the analysis input text."""
    if text.title:
        return f"{text.title}\n\n{text.body}".strip()
    return text.body.strip()


async def _analyze_kind(
    kind: AnalysisKind,
    req: AnalyzeRequest,
    text: TargetText,
) -> AnalyzeResult:
    """Run a single kind and build its :class:`AnalyzeResult`."""
    settings = get_settings()
    language = req.language or text.language
    combined = _result_text(text)

    if kind == AnalysisKind.EMBEDDING:
        vector = await embed_text(combined)
        return AnalyzeResult(
            target_type=req.target_type,
            target_id=req.target_id,
            kind=kind,
            provider=settings.embedding_provider,
            model=settings.embedding_model,
            result={},
            embedding=vector,
        )

    if kind in _LLM_KINDS:
        payload = await analyze(kind, combined, title=text.title, language=language)
        return AnalyzeResult(
            target_type=req.target_type,
            target_id=req.target_id,
            kind=kind,
            provider=settings.llm_provider,
            model=settings.llm_model,
            result=payload,
        )

    raise ValueError(f"Analyzer does not support kind {kind!r}")


def _dead_letter_payload(raw_value: Any, error: Exception, *, kind: str | None = None) -> dict:
    payload: dict[str, Any] = {
        "stage": "analyzer",
        "topic": str(Topic.ANALYZE_REQUESTS),
        "error_type": type(error).__name__,
        "error": str(error),
        "original": raw_value,
    }
    if kind is not None:
        payload["kind"] = kind
    return payload


async def _handle_message(producer: AIOKafkaProducer, raw_value: Any) -> None:
    """Process one request: publish an AnalyzeResult per kind, or dead-letter.

    A failure resolving the request/target dead-letters the whole message. A
    failure on an individual kind dead-letters just that kind and continues, so
    one bad analysis doesn't drop the others.
    """
    try:
        req = AnalyzeRequest.model_validate(raw_value)
        text = await _load_target_text(req.target_type, req.target_id)
    except Exception as exc:
        log.warning(
            "analyze.request_failed",
            error=str(exc),
            error_type=type(exc).__name__,
        )
        await producer.send_and_wait(str(Topic.DEAD_LETTER), _dead_letter_payload(raw_value, exc))
        return

    for kind in req.kinds:
        try:
            result = await _analyze_kind(kind, req, text)
        except Exception as exc:
            log.warning(
                "analyze.kind_failed",
                target_id=req.target_id,
                kind=str(kind),
                error=str(exc),
                error_type=type(exc).__name__,
            )
            await producer.send_and_wait(
                str(Topic.DEAD_LETTER),
                _dead_letter_payload(raw_value, exc, kind=str(kind)),
            )
            continue
        await publish(
            producer,
            Topic.ANALYZE_RESULTS,
            result,
            key=f"{req.target_type}:{req.target_id}",
        )
        log.info(
            "analyze.published",
            target_id=req.target_id,
            target_type=req.target_type,
            kind=str(kind),
        )


async def run() -> None:
    """Run the analyzer consumer loop until cancelled.

    Wired by the orchestrator (``newskoo.workers.run``). At-least-once delivery:
    offsets commit after each message is handled, and downstream persistence is
    idempotent on (target, kind, provider).
    """
    consumer: AIOKafkaConsumer = await make_consumer(
        Topic.ANALYZE_REQUESTS, group=_CONSUMER_GROUP
    )
    producer: AIOKafkaProducer = await make_producer()
    log.info("analyze.worker_started", group=_CONSUMER_GROUP)
    try:
        async for msg in consumer:
            try:
                await _handle_message(producer, msg.value)
            except Exception as exc:  # keep the loop alive on broker hiccups
                log.error("analyze.handle_unrecoverable", error=str(exc))
                continue
            await consumer.commit()
    finally:
        await consumer.stop()
        await producer.stop()
        log.info("analyze.worker_stopped", group=_CONSUMER_GROUP)


if __name__ == "__main__":  # pragma: no cover
    import asyncio

    asyncio.run(run())
