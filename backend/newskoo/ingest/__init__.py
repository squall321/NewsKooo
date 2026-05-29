"""Ingestion (Phase 3): RSS/feed collectors, API connectors (GDELT/NewsAPI),
HTML crawlers (httpx + Playwright), and the politeness engine. Produces
``RawDocument`` to Kafka ``raw.documents``."""

from __future__ import annotations

from newskoo.ingest.api import ApiConnector
from newskoo.ingest.html import HtmlConnector, PlaywrightCrawler
from newskoo.ingest.politeness import PolitenessEngine
from newskoo.ingest.producer import build_raw_document, emit_raw
from newskoo.ingest.rss import RssConnector
from newskoo.ingest.scheduler import build_scheduler, run_collection_cycle
from newskoo.ingest.worker import run

__all__ = [
    "ApiConnector",
    "HtmlConnector",
    "PlaywrightCrawler",
    "PolitenessEngine",
    "RssConnector",
    "build_raw_document",
    "build_scheduler",
    "emit_raw",
    "run",
    "run_collection_cycle",
]
