"""Event (clustered real-world story) models."""

from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Float, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from newskoo.core.config import get_settings
from newskoo.models.base import Base, PKMixin, TimestampMixin

_EMBED_DIM = get_settings().embedding_dim


class Event(Base, PKMixin, TimestampMixin):
    __tablename__ = "events"

    title: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(nullable=True)
    article_count: Mapped[int] = mapped_column(Integer, default=0)
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    language_count: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float] = mapped_column(Float, default=0.0)  # issue strength
    centroid: Mapped[list[float] | None] = mapped_column(Vector(_EMBED_DIM), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)

    articles = relationship(
        "Article", back_populates="event", foreign_keys="Article.event_id"
    )


class EventArticle(Base):
    __tablename__ = "event_articles"

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), primary_key=True
    )
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True
    )
    similarity: Mapped[float] = mapped_column(Float, default=0.0)
    is_seed: Mapped[bool] = mapped_column(Boolean, default=False)
