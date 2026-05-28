"""Per-fetch crawl log (feeds source health + politeness tuning)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from newskoo.models.base import Base, PKMixin


class CrawlLog(Base, PKMixin):
    __tablename__ = "crawl_log"

    source_id: Mapped[int | None] = mapped_column(
        ForeignKey("sources.id", ondelete="SET NULL"), nullable=True
    )
    url: Mapped[str] = mapped_column(Text)
    method: Mapped[str] = mapped_column(String(10))  # rss|api|html
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bytes: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    ok: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime]

    __table_args__ = (Index("ix_crawl_log_source_time", "source_id", "fetched_at"),)
