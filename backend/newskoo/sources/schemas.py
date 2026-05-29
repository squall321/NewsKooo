"""Pydantic v2 DTOs for the source registry.

These mirror the frozen :class:`newskoo.models.source.Source` ORM but stay
decoupled from it: ``SourceOut`` is the read model (``from_attributes``),
``SourceCreate`` / ``SourceUpdate`` are the write models, and
``PolitenessPolicy`` is the typed shape of the ``Source.politeness`` jsonb blob.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FetchMethod(StrEnum):
    """How a source is collected. Mirrors ``Source.fetch_method``."""

    RSS = "rss"
    API = "api"
    HTML = "html"


class PolitenessPolicy(BaseModel):
    """Per-source crawl politeness. Serialized into ``Source.politeness`` jsonb.

    Defaults are conservative; the politeness/ingestion engine (Phase 3) reads
    these to drive the per-domain token bucket and concurrency limits.
    """

    rps: float = Field(default=0.5, gt=0, le=20, description="requests/sec per domain")
    jitter_s: float = Field(default=0.5, ge=0, le=30, description="randomized delay seconds")
    max_concurrency: int = Field(default=2, ge=1, le=64)
    respect_robots: bool = True


# Politeness tiers keyed by ``bot_sensitivity`` (0 normal … 3 very sensitive).
_POLITENESS_TIERS: dict[int, PolitenessPolicy] = {
    0: PolitenessPolicy(rps=1.0, jitter_s=0.25, max_concurrency=4, respect_robots=True),
    1: PolitenessPolicy(rps=0.5, jitter_s=0.5, max_concurrency=2, respect_robots=True),
    2: PolitenessPolicy(rps=0.2, jitter_s=1.5, max_concurrency=1, respect_robots=True),
    3: PolitenessPolicy(rps=0.1, jitter_s=3.0, max_concurrency=1, respect_robots=True),
}


def politeness_for(bot_sensitivity: int) -> PolitenessPolicy:
    """Return a default politeness policy for a bot-sensitivity tier (0..3)."""
    tier = max(0, min(3, bot_sensitivity))
    return _POLITENESS_TIERS[tier].model_copy()


class _SourceBase(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    homepage_url: str = Field(min_length=1)
    feed_url: str | None = None
    api_kind: str | None = Field(default=None, max_length=40)
    fetch_method: FetchMethod
    region: str | None = Field(default=None, max_length=40)
    languages: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    bot_sensitivity: int = Field(default=0, ge=0, le=3)
    politeness: dict = Field(default_factory=dict)
    robots_url: str | None = None
    enabled: bool = True

    @field_validator("languages", "categories")
    @classmethod
    def _strip_and_dedupe(cls, v: list[str]) -> list[str]:
        seen: list[str] = []
        for item in v:
            cleaned = item.strip()
            if cleaned and cleaned not in seen:
                seen.append(cleaned)
        return seen


class SourceCreate(_SourceBase):
    """Write model for inserting a source. ``feed_url`` is required for ``rss``."""

    @model_validator(mode="after")
    def _feed_url_required_for_rss(self) -> Self:
        if self.fetch_method == FetchMethod.RSS and not self.feed_url:
            raise ValueError("feed_url is required when fetch_method == 'rss'")
        return self


class SourceUpdate(BaseModel):
    """Partial update model — every field optional; only set fields are applied."""

    name: str | None = Field(default=None, min_length=1, max_length=300)
    homepage_url: str | None = Field(default=None, min_length=1)
    feed_url: str | None = None
    api_kind: str | None = Field(default=None, max_length=40)
    fetch_method: FetchMethod | None = None
    region: str | None = Field(default=None, max_length=40)
    languages: list[str] | None = None
    categories: list[str] | None = None
    bot_sensitivity: int | None = Field(default=None, ge=0, le=3)
    politeness: dict | None = None
    robots_url: str | None = None
    enabled: bool | None = None
    health: dict | None = None


class SourceOut(_SourceBase):
    """Read model produced from the ORM via ``from_attributes``."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    health: dict = Field(default_factory=dict)
