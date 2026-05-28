"""Frozen inter-stage contracts.

These Pydantic models are the payloads exchanged over Kafka between pipeline
stages. They are intentionally stable: changing a field is a breaking change
across producers/consumers, so version via ``schema_version`` and additive
fields. Topic names live in :class:`Topic`.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Topic(StrEnum):
    """Kafka topic names (see docs/ARCHITECTURE.md §2)."""

    RAW_DOCUMENTS = "raw.documents"
    PARSED_ARTICLES = "parsed.articles"
    DEDUP_EVENTS = "dedup.events"
    ANALYZE_REQUESTS = "analyze.requests"
    ANALYZE_RESULTS = "analyze.results"
    ISSUES_ALERTS = "issues.alerts"
    DEAD_LETTER = "dead.letter"


SCHEMA_VERSION = 1


class _Msg(BaseModel):
    schema_version: int = SCHEMA_VERSION


class FetchMethod(StrEnum):
    RSS = "rss"
    API = "api"
    HTML = "html"


class RawDocument(_Msg):
    """Output of collectors → input to parser. Topic: ``raw.documents``."""

    source_id: int
    url: str
    canonical_url: str | None = None
    fetch_method: FetchMethod
    http_status: int | None = None
    content_type: str | None = None
    raw_html: str | None = None  # for HTML/RSS
    raw_text: str | None = None  # for API payloads already-clean
    title_hint: str | None = None
    published_at_hint: datetime | None = None
    fetched_at: datetime
    headers: dict[str, str] = Field(default_factory=dict)


class ParsedArticle(_Msg):
    """Output of parser → input to dedup/persist. Topic: ``parsed.articles``."""

    source_id: int
    url: str
    canonical_url: str
    title: str
    body: str
    language: str | None = None
    authors: list[str] = Field(default_factory=list)
    published_at: datetime | None = None
    fetched_at: datetime
    content_hash: str  # hex sha256 of normalized body
    simhash: int | None = None
    word_count: int = 0


class DedupEvent(_Msg):
    """Output of dedup/cluster. Topic: ``dedup.events``."""

    article_id: int
    canonical_url: str
    simhash: int
    is_duplicate: bool
    event_id: int | None = None
    near_duplicate_ids: list[int] = Field(default_factory=list)


class AnalysisKind(StrEnum):
    ENTITIES = "entities"
    KEYWORDS = "keywords"
    TOPICS = "topics"
    SENTIMENT = "sentiment"
    SUMMARY = "summary"
    TRANSLATION = "translation"
    EMBEDDING = "embedding"


class AnalyzeRequest(_Msg):
    """Request LLM/embedding analysis. Topic: ``analyze.requests``."""

    target_type: str  # "article" | "event"
    target_id: int
    kinds: list[AnalysisKind]
    language: str | None = None


class AnalyzeResult(_Msg):
    """Analysis output to persist. Topic: ``analyze.results``."""

    target_type: str
    target_id: int
    kind: AnalysisKind
    provider: str
    model: str
    result: dict  # kind-specific structured payload
    embedding: list[float] | None = None
    tokens: int = 0
    cost_usd: float = 0.0


class IssueAlert(_Msg):
    """Emerging-issue signal. Topic: ``issues.alerts``."""

    target_type: str  # "entity" | "topic" | "keyword"
    target_id: int
    label: str
    score: float  # anomaly strength (e.g. z-score)
    window_start: datetime
    window_end: datetime
    mention_count: int
    velocity: float
    supporting_article_ids: list[int] = Field(default_factory=list)
    supporting_event_ids: list[int] = Field(default_factory=list)


ALL_TOPICS: tuple[Topic, ...] = tuple(Topic)
