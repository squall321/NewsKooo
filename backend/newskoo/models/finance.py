"""Financial / equities models: the signal layer's persistent backbone.

This is the storage side of NewsKoo's ultimate goal — turning news into
tradeable signals. Three tables:

* :class:`Security` — the tradeable-instrument catalog (equities, ETFs, indices,
  ADRs, crypto, …). The signal layer's analogue of :class:`~newskoo.models.taxonomy.Entity`
  but keyed on a market ``symbol`` rather than a free-text name. Carries an
  optional embedding so a security can sit in the same semantic space as
  articles/entities/events (cross-language ticker disambiguation, semantic
  recall).
* :class:`EntitySecurity` — the bridge from the *news* world (:class:`Entity`)
  to the *market* world (:class:`Security`). One organisation/product/ticker
  entity may map to one or more securities (e.g. an Entity "Alphabet" → both
  GOOGL and GOOG) with a match ``confidence``.
* :class:`Signal` — a point-in-time, per-security, per-horizon tradeable signal
  derived from recent news impact. Signed ``score`` in [-1, 1], a categorical
  ``direction``, plus ``magnitude``/``confidence`` and a ``components`` audit
  trail and the supporting article/event ids (provenance for backtesting and UI
  drill-down).

All three follow the frozen ORM conventions (PKMixin/TimestampMixin, BigInteger
PKs, JSONB ``metadata``/``components``, ``Vector(embedding_dim)`` for embeddings).
The matching hand-written migration lives in ``alembic/versions/0002_finance.py``.
"""

from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from newskoo.core.config import get_settings
from newskoo.models.base import Base, PKMixin, TimestampMixin

_EMBED_DIM = get_settings().embedding_dim


class Security(Base, PKMixin, TimestampMixin):
    """A tradeable instrument (equity / etf / index / adr / crypto / …).

    ``symbol`` is the unique market identifier (e.g. ``"AAPL"``, ``"005930.KS"``,
    ``"^GSPC"``). ``aliases`` hold alternate surface forms used to link news
    :class:`Entity` rows to this security (full names, former names, common
    abbreviations). The optional ``embedding`` places the security in the shared
    multilingual vector space.
    """

    __tablename__ = "securities"

    symbol: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(400))
    exchange: Mapped[str | None] = mapped_column(String(40), nullable=True)
    mic: Mapped[str | None] = mapped_column(String(8), nullable=True)  # ISO 10383 market id
    country: Mapped[str | None] = mapped_column(String(8), nullable=True)  # ISO country code
    asset_class: Mapped[str] = mapped_column(String(20))  # equity|etf|index|adr|crypto|...
    aliases: Mapped[list[str]] = mapped_column(ARRAY(String(400)), default=list)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(_EMBED_DIM), nullable=True)

    __table_args__ = (
        Index("ix_securities_symbol", "symbol", unique=True),
        Index("ix_securities_name", "name"),
        # HNSW vector index on embedding is created in the Alembic migration.
    )


class EntitySecurity(Base):
    """M:N bridge linking a news :class:`Entity` to a market :class:`Security`.

    Written by :func:`newskoo.signals.securities.link_entities_to_securities`;
    ``confidence`` records how strong the (symbol/name/alias) match was so the
    signal generator can weight or filter weak links. Composite PK so a given
    (entity, security) pair is recorded at most once.
    """

    __tablename__ = "entity_securities"

    entity_id: Mapped[int] = mapped_column(
        ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True
    )
    security_id: Mapped[int] = mapped_column(
        ForeignKey("securities.id", ondelete="CASCADE"), primary_key=True
    )
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    __table_args__ = (Index("ix_entity_securities_security", "security_id"),)


class Signal(Base):
    """A point-in-time tradeable signal for one security over one horizon.

    ``score`` is signed in [-1, 1] (the directional conviction); ``direction``
    is its categorical projection (bullish/bearish/neutral); ``magnitude`` in
    [0, 1] is the unsigned strength; ``confidence`` in [0, 1] reflects sample
    size and agreement among the supporting articles. ``components`` is a JSONB
    audit dict (the decayed sub-impacts that produced the score), and the
    ``supporting_*_ids`` arrays are provenance for backtesting / UI drill-down.

    No ``updated_at``: signals are append-only point-in-time snapshots keyed by
    ``as_of`` — a re-run produces a *new* row, never mutates an old one. Hence
    this model uses :class:`PKMixin` only and declares its own ``created_at``.
    """

    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    security_id: Mapped[int] = mapped_column(
        ForeignKey("securities.id", ondelete="CASCADE")
    )
    as_of: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    horizon_hours: Mapped[int] = mapped_column(Integer)
    score: Mapped[float] = mapped_column(Float)  # signed, [-1, 1]
    direction: Mapped[str] = mapped_column(String(10))  # bullish|bearish|neutral
    magnitude: Mapped[float] = mapped_column(Float)  # [0, 1]
    confidence: Mapped[float] = mapped_column(Float)  # [0, 1]
    components: Mapped[dict] = mapped_column(JSONB, default=dict)
    supporting_article_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), default=list)
    supporting_event_ids: Mapped[list[int]] = mapped_column(ARRAY(BigInteger), default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (Index("ix_signals_security_as_of", "security_id", "as_of"),)
