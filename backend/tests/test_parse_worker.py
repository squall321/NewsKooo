"""Parser worker tests: message handling, publishing, dead-lettering.

No live Kafka — a fake producer records ``send_and_wait`` calls. The consume
loop itself (``run``) is not started; we test the per-message handler and the
pure ``parse_document`` transform that it drives.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from newskoo.core.contracts import FetchMethod, ParsedArticle, RawDocument, Topic
from newskoo.parse.worker import _handle_message

_HTML = """<html><head><title>City council approves new transit budget</title></head>
<body><article><h1>City council approves new transit budget</h1>
<p>The city council voted on Wednesday to approve a substantially expanded
transit budget that funds new bus routes and extended late-night service across
several neighborhoods beginning this autumn.</p></article></body></html>"""


class FakeProducer:
    """Records publishes; mimics ``send_and_wait`` and ``publish`` usage."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, Any, bytes | None]] = []

    async def send_and_wait(
        self, topic: str, value: Any, *, key: bytes | None = None
    ) -> None:
        self.sent.append((topic, value, key))

    def topics(self) -> list[str]:
        return [t for t, _v, _k in self.sent]


def _raw_doc(**overrides: object) -> RawDocument:
    base: dict[str, object] = {
        "source_id": 3,
        "url": "https://city.example.com/transit",
        "fetch_method": FetchMethod.HTML,
        "raw_html": _HTML,
        "fetched_at": datetime(2026, 5, 29, 8, 0, tzinfo=UTC),
    }
    base.update(overrides)
    return RawDocument(**base)  # type: ignore[arg-type]


async def test_handle_message_publishes_parsed_article() -> None:
    producer = FakeProducer()
    doc = _raw_doc()

    await _handle_message(producer, doc.model_dump(mode="json"))

    assert producer.topics() == [str(Topic.PARSED_ARTICLES)]
    _topic, value, key = producer.sent[0]
    # publish() passes the Pydantic model through to the producer serializer.
    assert isinstance(value, ParsedArticle)
    assert value.source_id == 3
    assert "transit budget" in value.body
    assert value.word_count > 0
    assert value.content_hash and len(value.content_hash) == 64
    assert key == value.canonical_url.encode()


async def test_handle_message_dead_letters_invalid_payload() -> None:
    producer = FakeProducer()

    # Missing required fields → validation error → dead-letter, not a crash.
    await _handle_message(producer, {"not": "a valid raw document"})

    assert producer.topics() == [str(Topic.DEAD_LETTER)]
    _topic, payload, _key = producer.sent[0]
    assert payload["stage"] == "parser"
    assert payload["topic"] == str(Topic.RAW_DOCUMENTS)
    assert "error" in payload and payload["error_type"]
    assert payload["original"] == {"not": "a valid raw document"}


async def test_handle_message_dead_letters_empty_document() -> None:
    producer = FakeProducer()
    doc = _raw_doc(raw_html=None, raw_text=None)

    await _handle_message(producer, doc.model_dump(mode="json"))

    assert producer.topics() == [str(Topic.DEAD_LETTER)]
    _topic, payload, _key = producer.sent[0]
    assert payload["error_type"] == "ValueError"


async def test_handle_message_propagates_producer_failure() -> None:
    # If dead-lettering itself fails, the error propagates so the loop won't
    # commit past an unhandled message.
    class BoomProducer(FakeProducer):
        async def send_and_wait(self, *a: Any, **k: Any) -> None:
            raise RuntimeError("broker down")

    producer = BoomProducer()
    with pytest.raises(RuntimeError, match="broker down"):
        await _handle_message(producer, {"bad": "payload"})
