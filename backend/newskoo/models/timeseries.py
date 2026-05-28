"""Pre-aggregated mention time series powering trends + issue detection."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from newskoo.models.base import Base


class MentionTimeseries(Base):
    __tablename__ = "mention_timeseries"

    target_type: Mapped[str] = mapped_column(String(10), primary_key=True)  # entity|topic|keyword
    target_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bucket: Mapped[datetime] = mapped_column(primary_key=True)  # e.g. hourly
    count: Mapped[int] = mapped_column(Integer, default=0)
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    velocity: Mapped[float] = mapped_column(Float, default=0.0)
    zscore: Mapped[float] = mapped_column(Float, default=0.0)
