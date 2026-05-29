"""Pydantic v2 request/response DTOs for the HTTP API.

These are the *wire* shapes the API exposes. Read models use
``from_attributes`` so they can be built directly from ORM rows
(``Model.model_validate(orm_obj)``); they stay decoupled from the frozen ORM so
the public contract can evolve without touching ``models/*``.

Conventions:
- ``*Out`` — response models (``from_attributes``).
- ``*Request`` — POST request bodies.
- :class:`Paginated` — generic envelope ``{items, total, limit, offset}``.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


# ── Generic pagination envelope ──────────────────────────────────────────────
class Paginated[T](BaseModel):
    """Generic page of ``items`` plus the paging window that produced it.

    ``total`` is the unfiltered-by-page count when known; endpoints that cannot
    cheaply count may set it to the number of returned items.
    """

    items: list[T]
    total: int = 0
    limit: int = 50
    offset: int = 0


# ── Sources ──────────────────────────────────────────────────────────────────
class SourceOut(BaseModel):
    """Source registry read model."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    homepage_url: str
    feed_url: str | None = None
    api_kind: str | None = None
    fetch_method: str
    region: str | None = None
    languages: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    bot_sensitivity: int = 0
    politeness: dict = Field(default_factory=dict)
    robots_url: str | None = None
    enabled: bool = True
    health: dict = Field(default_factory=dict)


# ── Articles ─────────────────────────────────────────────────────────────────
class EntityRef(BaseModel):
    """An entity mentioned by an article, with per-article weighting."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    salience: float = 0.0
    sentiment: float | None = None


class TopicRef(BaseModel):
    """A topic an article is classified under, with confidence."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    label: str
    confidence: float = 0.0


class ArticleOut(BaseModel):
    """Article read model. ``entities``/``topics`` are populated only on detail."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    canonical_url: str
    url: str
    title: str
    language: str | None = None
    authors: list[str] = Field(default_factory=list)
    published_at: datetime | None = None
    fetched_at: datetime
    word_count: int = 0
    status: str = "parsed"
    event_id: int | None = None
    # Body is heavy; included on detail/feed but trimmable by callers.
    body: str | None = None
    entities: list[EntityRef] = Field(default_factory=list)
    topics: list[TopicRef] = Field(default_factory=list)
    # Present on search responses (relevance / distance), else None.
    score: float | None = None


# ── Events ───────────────────────────────────────────────────────────────────
class EventArticleRef(BaseModel):
    """A member article of an event, with cluster similarity."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source_id: int
    language: str | None = None
    published_at: datetime | None = None
    similarity: float = 0.0
    is_seed: bool = False


class EventOut(BaseModel):
    """Event (clustered story) read model. ``articles`` set only on detail."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    summary: str | None = None
    started_at: datetime | None = None
    last_seen_at: datetime | None = None
    article_count: int = 0
    source_count: int = 0
    language_count: int = 0
    score: float = 0.0
    articles: list[EventArticleRef] = Field(default_factory=list)


# ── Trends / issues ──────────────────────────────────────────────────────────
class TrendPoint(BaseModel):
    """One bucket of a mention time-series (powers trend/velocity charts)."""

    model_config = ConfigDict(from_attributes=True)

    bucket: datetime
    count: int = 0
    source_count: int = 0
    velocity: float = 0.0
    zscore: float = 0.0


class TrendSeries(BaseModel):
    """A target's full trend series over the requested window."""

    target_type: str
    target_id: int
    label: str
    points: list[TrendPoint] = Field(default_factory=list)


class IssueOut(BaseModel):
    """An emerging-issue alert derived from spiking mention buckets."""

    target_type: str  # entity | topic | keyword
    target_id: int
    label: str
    score: float
    window_start: datetime
    window_end: datetime
    mention_count: int
    velocity: float
    supporting_article_ids: list[int] = Field(default_factory=list)
    supporting_event_ids: list[int] = Field(default_factory=list)


# ── Reports ──────────────────────────────────────────────────────────────────
class ReportOut(BaseModel):
    """Generated intelligence report read model."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    query: dict = Field(default_factory=dict)
    title: str
    body_md: str
    citations: dict = Field(default_factory=dict)
    provider: str | None = None
    model: str | None = None
    scheduled: bool = False
    version: int = 1
    created_at: datetime | None = None


# ── Search request ───────────────────────────────────────────────────────────
class SearchMode(StrEnum):
    FTS = "fts"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"


class SearchRequest(BaseModel):
    """Article search request.

    ``window`` is an optional ISO-8601 duration-ish hint expressed in hours; the
    search router treats it as "only the last N hours by ``published_at``".
    """

    q: str = Field(min_length=1, max_length=1000)
    mode: SearchMode = SearchMode.HYBRID
    window: int | None = Field(
        default=None, ge=1, le=24 * 365, description="lookback in hours"
    )
    limit: int = Field(default=20, ge=1, le=100)
    source_id: int | None = None
    language: str | None = None
    topic_id: int | None = None


# ── Report request ───────────────────────────────────────────────────────────
class ReportRequest(BaseModel):
    """On-demand report generation request."""

    keywords: list[str] = Field(default_factory=list)
    sector: str | None = None
    region: str | None = None
    window: int | None = Field(
        default=168, ge=1, le=24 * 365, description="lookback in hours"
    )

    def to_query(self) -> dict:
        """Normalize to the ``ReportQuery`` shape (window expressed in hours)."""
        return {
            "keywords": self.keywords,
            "sector": self.sector,
            "region": self.region,
            "window_hours": self.window,
        }
