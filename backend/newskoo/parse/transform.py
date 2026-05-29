"""Assemble a frozen :class:`ParsedArticle` from extraction + detection output.

Bridges the loosely-typed extraction result and the :class:`RawDocument`
envelope into the frozen ``parsed.articles`` contract: computes the content hash
(hex sha256 of the normalized body via :mod:`newskoo.core.accel`), the 64-bit
simhash, word count, and resolves canonical URL / published-at / fetched-at with
sensible fallbacks.
"""

from __future__ import annotations

from datetime import datetime

from newskoo.core import accel
from newskoo.core.contracts import ParsedArticle, RawDocument
from newskoo.parse.extract import ExtractedArticle


def _word_count(body: str) -> int:
    """Whitespace-token count of the (normalized) body."""
    if not body:
        return 0
    return len(accel.normalize(body).split())


def to_parsed_article(
    doc: RawDocument,
    extracted: ExtractedArticle,
    language: str | None,
) -> ParsedArticle:
    """Build a :class:`ParsedArticle` from a raw document and its extraction.

    Field resolution:

    * ``canonical_url`` — extraction's canonical → ``doc.canonical_url`` →
      ``doc.url`` (never empty; satisfies the frozen contract).
    * ``title`` — extraction title → ``doc.title_hint`` → ``""``.
    * ``content_hash`` — hex sha256 of the normalized body (revision detection).
    * ``simhash`` — 64-bit simhash of the body (near-duplicate detection).
    * ``published_at`` — extracted date → ``doc.published_at_hint``.
    * ``fetched_at`` — carried straight from the raw document.
    """
    body = extracted.body or ""

    canonical = (
        (extracted.canonical_url or "").strip()
        or (doc.canonical_url or "").strip()
        or doc.url
    )
    title = (extracted.title or "").strip() or (doc.title_hint or "").strip()
    published_at: datetime | None = extracted.published_at or doc.published_at_hint

    content_hash_hex = accel.content_hash(body).hex()
    simhash = accel.simhash64(body) if body.strip() else None

    return ParsedArticle(
        source_id=doc.source_id,
        url=doc.url,
        canonical_url=canonical,
        title=title,
        body=body,
        language=language,
        authors=list(extracted.authors),
        published_at=published_at,
        fetched_at=doc.fetched_at,
        content_hash=content_hash_hex,
        simhash=simhash,
        word_count=_word_count(body),
    )
