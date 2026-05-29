"""Parsing/extraction (Phase 4): article extraction (trafilatura), language
detection, normalization + simhash (C++ accel). Consumes ``raw.documents`` and
produces ``parsed.articles``."""

from __future__ import annotations

from newskoo.parse.extract import ExtractedArticle, extract_article
from newskoo.parse.language import detect_language
from newskoo.parse.transform import to_parsed_article
from newskoo.parse.worker import parse_document, run

__all__ = [
    "ExtractedArticle",
    "detect_language",
    "extract_article",
    "parse_document",
    "run",
    "to_parsed_article",
]
