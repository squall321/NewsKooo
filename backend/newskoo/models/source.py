"""Source registry model."""

from __future__ import annotations

from sqlalchemy import ARRAY, Boolean, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from newskoo.models.base import Base, PKMixin, TimestampMixin


class Source(Base, PKMixin, TimestampMixin):
    __tablename__ = "sources"

    name: Mapped[str] = mapped_column(String(300))
    homepage_url: Mapped[str] = mapped_column(Text)
    feed_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    api_kind: Mapped[str | None] = mapped_column(String(40), nullable=True)
    fetch_method: Mapped[str] = mapped_column(String(10))  # rss|api|html
    region: Mapped[str | None] = mapped_column(String(40), nullable=True)
    languages: Mapped[list[str]] = mapped_column(ARRAY(String(8)), default=list)
    categories: Mapped[list[str]] = mapped_column(ARRAY(String(40)), default=list)
    bot_sensitivity: Mapped[int] = mapped_column(SmallInteger, default=0)  # 0..3
    politeness: Mapped[dict] = mapped_column(JSONB, default=dict)
    robots_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    health: Mapped[dict] = mapped_column(JSONB, default=dict)
