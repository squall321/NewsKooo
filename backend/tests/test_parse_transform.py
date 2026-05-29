"""Transform tests: RawDocument → ParsedArticle (hashes, counts, fallbacks).

No network/Kafka. Exercises both the HTML path (via ``parse_document``) and the
direct ``to_parsed_article`` assembly.
"""

from __future__ import annotations

from datetime import UTC, datetime

from newskoo.core import accel
from newskoo.core.contracts import FetchMethod, RawDocument
from newskoo.parse.extract import ExtractedArticle
from newskoo.parse.transform import to_parsed_article
from newskoo.parse.worker import parse_document

_HTML = """<html><head><title>Quarterly earnings beat estimates</title></head>
<body><article>
<h1>Quarterly earnings beat estimates</h1>
<p>The company reported quarterly revenue well above analyst expectations,
driven by strong demand across its cloud and advertising segments during the
period under review.</p>
<p>Executives raised full-year guidance and announced an expanded share
repurchase program, sending the stock higher in after-hours trading.</p>
</article></body></html>"""


def _raw_html_doc(**overrides: object) -> RawDocument:
    base: dict[str, object] = {
        "source_id": 7,
        "url": "https://biz.example.com/earnings",
        "fetch_method": FetchMethod.HTML,
        "raw_html": _HTML,
        "fetched_at": datetime(2026, 5, 29, 12, 0, tzinfo=UTC),
    }
    base.update(overrides)
    return RawDocument(**base)  # type: ignore[arg-type]


def test_parsed_article_has_hex_content_hash() -> None:
    art = parse_document(_raw_html_doc())
    assert isinstance(art.content_hash, str)
    assert len(art.content_hash) == 64  # sha256 hex
    bytes.fromhex(art.content_hash)  # valid hex, raises otherwise


def test_parsed_article_content_hash_matches_accel() -> None:
    art = parse_document(_raw_html_doc())
    assert art.content_hash == accel.content_hash(art.body).hex()


def test_parsed_article_simhash_and_word_count_set() -> None:
    art = parse_document(_raw_html_doc())
    assert art.simhash is not None
    assert art.simhash == accel.simhash64(art.body)
    assert art.word_count > 0


def test_canonical_url_defaults_to_url() -> None:
    # No canonical in HTML/extraction and none on the doc → falls back to url.
    extracted = ExtractedArticle(title="t", body="some body text here", canonical_url=None)
    doc = _raw_html_doc(canonical_url=None)
    art = to_parsed_article(doc, extracted, "en")
    assert art.canonical_url == doc.url


def test_canonical_url_prefers_extracted() -> None:
    extracted = ExtractedArticle(
        title="t", body="body", canonical_url="https://canon.example.com/x"
    )
    art = to_parsed_article(_raw_html_doc(), extracted, "en")
    assert art.canonical_url == "https://canon.example.com/x"


def test_raw_text_api_payload_path() -> None:
    # API sources carry already-clean raw_text; extraction is bypassed.
    doc = _raw_html_doc(
        raw_html=None,
        raw_text="This is a clean API article body about technology and markets.",
        title_hint="API Title",
        fetch_method=FetchMethod.API,
        canonical_url="https://api.example.com/a",
    )
    art = parse_document(doc)
    assert art.title == "API Title"
    assert "clean API article body" in art.body
    assert art.canonical_url == "https://api.example.com/a"
    assert art.word_count > 0


def test_published_at_falls_back_to_doc_hint() -> None:
    hint = datetime(2026, 5, 1, 9, 0, tzinfo=UTC)
    extracted = ExtractedArticle(title="t", body="body", published_at=None)
    art = to_parsed_article(_raw_html_doc(published_at_hint=hint), extracted, "en")
    assert art.published_at == hint


def test_fetched_at_carried_from_doc() -> None:
    doc = _raw_html_doc()
    art = parse_document(doc)
    assert art.fetched_at == doc.fetched_at


def test_missing_body_raises() -> None:
    import pytest

    doc = _raw_html_doc(raw_html=None, raw_text=None)
    with pytest.raises(ValueError, match="neither"):
        parse_document(doc)
