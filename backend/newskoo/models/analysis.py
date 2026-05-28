"""Derived LLM analysis + generated reports."""

from __future__ import annotations

from sqlalchemy import Boolean, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from newskoo.models.base import Base, PKMixin, TimestampMixin


class Analysis(Base, PKMixin, TimestampMixin):
    __tablename__ = "analysis"

    target_type: Mapped[str] = mapped_column(String(10))  # article|event
    target_id: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(20))  # summary|sentiment|entities|...
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(120))
    result: Mapped[dict] = mapped_column(JSONB, default=dict)
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)

    __table_args__ = (
        Index("ix_analysis_target", "target_type", "target_id", "kind"),
    )


class Report(Base, PKMixin, TimestampMixin):
    __tablename__ = "reports"

    query: Mapped[dict] = mapped_column(JSONB, default=dict)  # keywords/sector/region/window
    title: Mapped[str] = mapped_column(Text)
    body_md: Mapped[str] = mapped_column(Text)
    citations: Mapped[dict] = mapped_column(JSONB, default=dict)  # {articles:[], events:[]}
    provider: Mapped[str | None] = mapped_column(String(40), nullable=True)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    scheduled: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
