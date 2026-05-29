"""Parser worker: ``raw.documents`` → ``parsed.articles``.

Consumer group that, for each :class:`RawDocument`:

1. extracts a boilerplate-free article (trafilatura → selectolax fallback),
   or uses ``raw_text`` directly for API payloads that are already clean;
2. detects the language;
3. transforms into the frozen :class:`ParsedArticle` (content hash + simhash +
   word count + canonical/date resolution);
4. publishes to ``parsed.articles`` keyed on ``canonical_url``.

Offsets are committed only after a message is fully handled (published or
dead-lettered). Per-message failures never crash the loop: the offending
document plus error context is routed to ``dead.letter``.
"""

from __future__ import annotations

from typing import Any

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from newskoo.core.contracts import ParsedArticle, RawDocument, Topic
from newskoo.core.kafka import make_consumer, make_producer, publish
from newskoo.core.logging import get_logger
from newskoo.parse.extract import ExtractedArticle, extract_article
from newskoo.parse.language import detect_language
from newskoo.parse.transform import to_parsed_article

log = get_logger(__name__)

_CONSUMER_GROUP = "parser"


def _extracted_from_raw_text(doc: RawDocument) -> ExtractedArticle:
    """Wrap an already-clean API ``raw_text`` payload as an extraction result."""
    return ExtractedArticle(
        title=(doc.title_hint or "").strip() or None,
        body=(doc.raw_text or "").strip(),
        authors=[],
        published_at=doc.published_at_hint,
        canonical_url=doc.canonical_url or doc.url,
    )


def parse_document(doc: RawDocument) -> ParsedArticle:
    """Pure transform: :class:`RawDocument` → :class:`ParsedArticle`.

    Prefers pre-cleaned ``raw_text`` (API sources) and otherwise extracts from
    ``raw_html``. Raises :class:`ValueError` when neither is present.
    """
    if doc.raw_text and doc.raw_text.strip():
        extracted = _extracted_from_raw_text(doc)
    elif doc.raw_html and doc.raw_html.strip():
        extracted = extract_article(doc.raw_html, doc.url)
    else:
        raise ValueError("RawDocument has neither raw_text nor raw_html")

    language = detect_language(extracted.body)
    return to_parsed_article(doc, extracted, language)


def _dead_letter_payload(raw_value: Any, error: Exception) -> dict[str, Any]:
    """Build a JSON-serializable dead-letter envelope with error context."""
    return {
        "stage": "parser",
        "topic": str(Topic.RAW_DOCUMENTS),
        "error_type": type(error).__name__,
        "error": str(error),
        "original": raw_value,
    }


async def _handle_message(
    producer: AIOKafkaProducer,
    raw_value: Any,
) -> None:
    """Process one raw message; publish the parsed article or dead-letter it.

    Any exception is converted into a ``dead.letter`` record so the consume loop
    can commit and move on. Re-raises only if dead-lettering itself fails.
    """
    try:
        doc = RawDocument.model_validate(raw_value)
        article = parse_document(doc)
    except Exception as exc:  # any failure becomes a dead-letter, not a crash
        log.warning(
            "parse.message_failed",
            error=str(exc),
            error_type=type(exc).__name__,
        )
        await producer.send_and_wait(
            str(Topic.DEAD_LETTER),
            _dead_letter_payload(raw_value, exc),
        )
        return

    await publish(
        producer,
        Topic.PARSED_ARTICLES,
        article,
        key=article.canonical_url,
    )
    log.info(
        "parse.published",
        source_id=article.source_id,
        canonical_url=article.canonical_url,
        language=article.language,
        word_count=article.word_count,
    )


async def run() -> None:
    """Run the parser consumer loop until cancelled.

    Wired by ``newskoo.workers.run`` (the orchestrator). Commits offsets after
    each message is handled (published or dead-lettered), giving at-least-once
    delivery with idempotent downstream upserts (canonical_url + content_hash).
    """
    consumer: AIOKafkaConsumer = await make_consumer(
        Topic.RAW_DOCUMENTS, group=_CONSUMER_GROUP
    )
    producer: AIOKafkaProducer = await make_producer()
    log.info("parse.worker_started", group=_CONSUMER_GROUP)
    try:
        async for msg in consumer:
            try:
                await _handle_message(producer, msg.value)
            except Exception as exc:  # keep the loop alive on broker hiccups
                # Dead-lettering failed (e.g. broker hiccup); log and retry the
                # message rather than committing past it.
                log.error("parse.handle_unrecoverable", error=str(exc))
                continue
            await consumer.commit()
    finally:
        await consumer.stop()
        await producer.stop()
        log.info("parse.worker_stopped", group=_CONSUMER_GROUP)
