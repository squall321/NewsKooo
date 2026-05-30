"""Financial signal + securities endpoints (read).

Exposes the signal layer: the securities catalog and the news-derived per-security
signals (latest, strongest, and per-security history). Generation is a worker/CLI
job (``python -m newskoo.signals.cli``); these endpoints serve the results.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from newskoo.api.deps import SessionDep
from newskoo.api.routers import LimitQuery, OffsetQuery
from newskoo.api.schemas import Paginated, SecurityOut, SignalOut
from newskoo.models.finance import Security, Signal

router = APIRouter(tags=["signals"])


@router.get("/securities", response_model=Paginated[SecurityOut])
async def list_securities(
    session: AsyncSession = SessionDep,
    q: str | None = Query(default=None, description="symbol/name substring"),
    asset_class: str | None = None,
    limit: int = LimitQuery,
    offset: int = OffsetQuery,
) -> Paginated[SecurityOut]:
    stmt = select(Security)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Security.symbol.ilike(like), Security.name.ilike(like)))
    if asset_class:
        stmt = stmt.where(Security.asset_class == asset_class)
    total = int(await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    rows = (
        await session.execute(stmt.order_by(Security.symbol).limit(limit).offset(offset))
    ).scalars().all()
    return Paginated[SecurityOut](
        items=[SecurityOut.model_validate(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/securities/{symbol}", response_model=SecurityOut)
async def get_security(symbol: str, session: AsyncSession = SessionDep) -> SecurityOut:
    row = (
        await session.execute(select(Security).where(Security.symbol == symbol))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "security not found")
    return SecurityOut.model_validate(row)


@router.get("/signals", response_model=Paginated[SignalOut])
async def list_signals(
    session: AsyncSession = SessionDep,
    security_id: int | None = None,
    min_abs_score: float = Query(default=0.0, ge=0.0, le=1.0),
    limit: int = LimitQuery,
    offset: int = OffsetQuery,
) -> Paginated[SignalOut]:
    """Most recent signals first (optionally filtered by security / strength)."""
    stmt = select(Signal)
    if security_id is not None:
        stmt = stmt.where(Signal.security_id == security_id)
    if min_abs_score > 0:
        stmt = stmt.where(func.abs(Signal.score) >= min_abs_score)
    total = int(await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    rows = (
        await session.execute(
            stmt.order_by(Signal.as_of.desc(), Signal.id.desc()).limit(limit).offset(offset)
        )
    ).scalars().all()
    return Paginated[SignalOut](
        items=[SignalOut.model_validate(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/signals/top", response_model=list[SignalOut])
async def top_signals(
    session: AsyncSession = SessionDep,
    window_hours: int = Query(default=72, ge=1, le=24 * 90),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[SignalOut]:
    """Strongest signals (by magnitude) within the recent window."""
    since = datetime.now(UTC) - timedelta(hours=window_hours)
    rows = (
        await session.execute(
            select(Signal)
            .where(Signal.as_of >= since)
            .order_by(Signal.magnitude.desc(), Signal.as_of.desc())
            .limit(limit)
        )
    ).scalars().all()
    return [SignalOut.model_validate(r) for r in rows]
