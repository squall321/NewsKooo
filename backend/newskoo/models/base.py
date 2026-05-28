"""SQLAlchemy declarative base + shared mixins.

NOTE on partitioning: docs/DATA_MODEL.md targets time-range partitioning for
``articles`` and ``crawl_log``. The ORM uses a single ``id`` primary key so
foreign keys stay simple; converting to native partitioning (pg_partman or
manual ``PARTITION BY RANGE (published_at)``) is a Phase-10 ops migration and
does not change these mappings.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PKMixin:
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
