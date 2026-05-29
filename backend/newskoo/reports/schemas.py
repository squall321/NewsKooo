"""Report query/result DTOs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ReportQuery(BaseModel):
    """A request to generate an intelligence report."""

    keywords: list[str] = Field(default_factory=list)
    sector: str | None = None
    region: str | None = None
    languages: list[str] = Field(default_factory=list)
    window_hours: int = 48  # look back this many hours
    max_events: int = 12  # how many events to synthesize over
    max_articles_per_event: int = 4
    title: str | None = None  # optional caller-supplied title


class Citation(BaseModel):
    articles: list[int] = Field(default_factory=list)
    events: list[int] = Field(default_factory=list)


class ReportResult(BaseModel):
    id: int | None = None
    title: str
    body_md: str
    citations: Citation
    provider: str | None = None
    model: str | None = None
    scheduled: bool = False
    version: int = 1
    created_at: datetime | None = None
