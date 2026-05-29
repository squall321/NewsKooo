"""Source registry endpoints.

Read endpoints are open; mutations require the API key (via ``AuthDep``) when
``settings.api_key`` is configured. CRUD is delegated to
:mod:`newskoo.sources.registry` so the HTTP layer stays thin and the same logic
is shared with the ingestion workers.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from newskoo.api.deps import AuthDep, SessionDep
from newskoo.api.routers import LimitQuery, OffsetQuery
from newskoo.api.schemas import Paginated, SourceOut
from newskoo.models.source import Source
from newskoo.sources import registry
from newskoo.sources.schemas import SourceCreate, SourceUpdate

router = APIRouter(prefix="/sources", tags=["sources"])


async def _count_sources(
    session: AsyncSession,
    *,
    enabled: bool | None,
    region: str | None,
    category: str | None,
) -> int:
    stmt = select(func.count()).select_from(Source)
    if enabled is not None:
        stmt = stmt.where(Source.enabled.is_(enabled))
    if region is not None:
        stmt = stmt.where(Source.region == region)
    if category is not None:
        stmt = stmt.where(Source.categories.any(category))
    return int(await session.scalar(stmt) or 0)


@router.get("", response_model=Paginated[SourceOut])
async def list_sources(
    session: AsyncSession = SessionDep,
    enabled: bool | None = None,
    region: str | None = None,
    category: str | None = None,
    limit: int = LimitQuery,
    offset: int = OffsetQuery,
) -> Paginated[SourceOut]:
    rows = await registry.list_sources(
        session,
        enabled=enabled,
        region=region,
        category=category,
        limit=limit,
        offset=offset,
    )
    total = await _count_sources(
        session, enabled=enabled, region=region, category=category
    )
    return Paginated[SourceOut](
        items=[SourceOut.model_validate(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{source_id}", response_model=SourceOut)
async def get_source(
    source_id: int, session: AsyncSession = SessionDep
) -> SourceOut:
    src = await registry.get_source(session, source_id)
    if src is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "source not found")
    return SourceOut.model_validate(src)


@router.post(
    "", response_model=SourceOut, status_code=status.HTTP_201_CREATED, dependencies=[AuthDep]
)
async def create_source(
    payload: SourceCreate, session: AsyncSession = SessionDep
) -> SourceOut:
    src = await registry.create_source(session, payload)
    await session.commit()
    return SourceOut.model_validate(src)


@router.patch("/{source_id}", response_model=SourceOut, dependencies=[AuthDep])
async def update_source(
    source_id: int, payload: SourceUpdate, session: AsyncSession = SessionDep
) -> SourceOut:
    src = await registry.update_source(session, source_id, payload)
    if src is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "source not found")
    await session.commit()
    return SourceOut.model_validate(src)


@router.post("/{source_id}/enable", response_model=SourceOut, dependencies=[AuthDep])
async def enable_source(
    source_id: int, session: AsyncSession = SessionDep
) -> SourceOut:
    src = await registry.set_enabled(session, source_id, True)
    if src is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "source not found")
    await session.commit()
    return SourceOut.model_validate(src)


@router.post("/{source_id}/disable", response_model=SourceOut, dependencies=[AuthDep])
async def disable_source(
    source_id: int, session: AsyncSession = SessionDep
) -> SourceOut:
    src = await registry.set_enabled(session, source_id, False)
    if src is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "source not found")
    await session.commit()
    return SourceOut.model_validate(src)
