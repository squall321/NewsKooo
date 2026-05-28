"""Foundation smoke tests — no live services required."""

from __future__ import annotations

from newskoo.core import accel
from newskoo.core.contracts import ALL_TOPICS, ParsedArticle, RawDocument, Topic


def test_simhash_near_duplicate_is_close() -> None:
    a = accel.simhash64("The quick brown fox jumps over the lazy dog")
    b = accel.simhash64("The quick brown fox jumps over the lazy dogs")  # near-dup
    c = accel.simhash64("Completely unrelated text about economics and markets")
    assert accel.hamming(a, b) < accel.hamming(a, c)


def test_normalize_collapses_whitespace_and_lowercases() -> None:
    assert accel.normalize("  Hello\t WORLD\n") == "hello world"


def test_content_hash_stable() -> None:
    assert accel.content_hash("Hello World") == accel.content_hash("hello   world")


def test_topics_enumerated() -> None:
    assert Topic.RAW_DOCUMENTS in ALL_TOPICS
    assert len(ALL_TOPICS) == len(set(ALL_TOPICS))


def test_contract_roundtrip() -> None:
    from datetime import datetime, timezone

    doc = RawDocument(
        source_id=1,
        url="https://example.com/a",
        fetch_method="html",
        raw_html="<html/>",
        fetched_at=datetime.now(timezone.utc),
    )
    restored = RawDocument.model_validate(doc.model_dump(mode="json"))
    assert restored.url == doc.url

    art = ParsedArticle(
        source_id=1,
        url="https://example.com/a",
        canonical_url="https://example.com/a",
        title="t",
        body="b",
        fetched_at=datetime.now(timezone.utc),
        content_hash="ab",
    )
    assert ParsedArticle.model_validate(art.model_dump(mode="json")).title == "t"
