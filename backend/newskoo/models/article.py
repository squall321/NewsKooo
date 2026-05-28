"""Article + revision-history models."""

from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    BigInteger,
    Computed,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from newskoo.core.config import get_settings
from newskoo.models.base import Base, PKMixin, TimestampMixin

_EMBED_DIM = get_settings().embedding_dim


class Article(Base, PKMixin, TimestampMixin):
    __tablename__ = "articles"

    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"))
    canonical_url: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    authors: Mapped[list[str]] = mapped_column(ARRAY(String(200)), default=list)
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)
    fetched_at: Mapped[datetime]
    content_hash: Mapped[bytes] = mapped_column(LargeBinary(32))
    simhash: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="parsed")
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("events.id", ondelete="SET NULL"), nullable=True
    )

    # Lexical full-text (language-agnostic 'simple' config; per-language later).
    tsv: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('simple', coalesce(title,'') || ' ' || coalesce(body,''))",
            persisted=True,
        ),
        nullable=True,
    )
    # Semantic embedding (nullable until the analyze stage fills it).
    embedding: Mapped[list[float] | None] = mapped_column(Vector(_EMBED_DIM), nullable=True)

    event = relationship("Event", back_populates="articles", foreign_keys=[event_id])

    __table_args__ = (
        Index("ix_articles_canonical_url", "canonical_url", unique=True),
        Index("ix_articles_source_published", "source_id", "published_at"),
        Index("ix_articles_simhash", "simhash"),
        Index("ix_articles_tsv", "tsv", postgresql_using="gin"),
        # ivfflat/hnsw vector index is created in the Alembic migration.
    )


class ArticleVersion(Base, PKMixin):
    __tablename__ = "article_versions"

    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE")
    )
    title: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[bytes] = mapped_column(LargeBinary(32))
    fetched_at: Mapped[datetime]
