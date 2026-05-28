"""Entities, keywords, topics and their article links."""

from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from newskoo.core.config import get_settings
from newskoo.models.base import Base, PKMixin, TimestampMixin

_EMBED_DIM = get_settings().embedding_dim


class Entity(Base, PKMixin, TimestampMixin):
    __tablename__ = "entities"

    name: Mapped[str] = mapped_column(String(400))
    type: Mapped[str] = mapped_column(String(40))  # person|org|product|place|ticker|...
    aliases: Mapped[list[str]] = mapped_column(ARRAY(String(400)), default=list)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(_EMBED_DIM), nullable=True)

    __table_args__ = (UniqueConstraint("name", "type", name="uq_entity_name_type"),)


class ArticleEntity(Base):
    __tablename__ = "article_entities"

    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True
    )
    entity_id: Mapped[int] = mapped_column(
        ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True
    )
    salience: Mapped[float] = mapped_column(Float, default=0.0)
    count: Mapped[int] = mapped_column(Integer, default=1)
    sentiment: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (Index("ix_article_entities_entity", "entity_id"),)


class Keyword(Base, PKMixin):
    __tablename__ = "keywords"

    term: Mapped[str] = mapped_column(String(200), unique=True)


class ArticleKeyword(Base):
    __tablename__ = "article_keywords"

    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True
    )
    keyword_id: Mapped[int] = mapped_column(
        ForeignKey("keywords.id", ondelete="CASCADE"), primary_key=True
    )
    weight: Mapped[float] = mapped_column(Float, default=0.0)

    __table_args__ = (Index("ix_article_keywords_keyword", "keyword_id"),)


class Topic(Base, PKMixin):
    __tablename__ = "topics"

    slug: Mapped[str] = mapped_column(String(120), unique=True)
    label: Mapped[str] = mapped_column(String(200))
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("topics.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class ArticleTopic(Base):
    __tablename__ = "article_topics"

    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True
    )
    topic_id: Mapped[int] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True
    )
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    __table_args__ = (Index("ix_article_topics_topic", "topic_id"),)
