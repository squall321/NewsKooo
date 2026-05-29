"""Event (clustered story) endpoints: list (top-by-score or recent) and detail
with member articles.

The list defaults to "top by issue strength" (``score`` desc) — the most useful
default for a "what's happening" view — with an ``order=recent`` switch to sort
by ``last_seen_at`` instead.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from newskoo.api.deps import SessionDep
from newskoo.api.routers import LimitQuery, OffsetQuery
from newskoo.api.schemas import EventArticleRef, EventOut, Paginated
from newskoo.models.article import Article
from newskoo.models.event import Event, EventArticle

router = APIRouter(prefix="/events", tags=["events"])


class EventOrder(StrEnum):
    SCORE = "score"
    RECENT = "recent"


@router.get("", response_model=Paginated[EventOut])
async def list_events(
    session: AsyncSession = SessionDep,
    order: EventOrder = EventOrder.SCORE,
    min_score: Annotated[float | None, Query(ge=0.0)] = None,
    limit: int = LimitQuery,
    offset: int = OffsetQuery,
) -> Paginated[EventOut]:
    stmt = select(Event)
    if min_score is not None:
        stmt = stmt.where(Event.score >= min_score)
    if order == EventOrder.RECENT:
        stmt = stmt.order_by(Event.last_seen_at.desc().nullslast(), Event.id.desc())
    else:
        stmt = stmt.order_by(Event.score.desc(), Event.id.desc())

    rows = (await session.execute(stmt.limit(limit).offset(offset))).scalars().all()

    count_stmt = select(func.count()).select_from(Event)
    if min_score is not None:
        count_stmt = count_stmt.where(Event.score >= min_score)
    total = int(await session.scalar(count_stmt) or 0)
    return Paginated[EventOut](
        items=[EventOut.model_validate(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{event_id}", response_model=EventOut)
async def get_event(
    event_id: int, session: AsyncSession = SessionDep
) -> EventOut:
    event = await session.get(Event, event_id)
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "event not found")
    out = EventOut.model_validate(event)

    stmt = (
        select(
            Article.id,
            Article.title,
            Article.source_id,
            Article.language,
            Article.published_at,
            EventArticle.similarity,
            EventArticle.is_seed,
        )
        .join(EventArticle, EventArticle.article_id == Article.id)
        .where(EventArticle.event_id == event_id)
        .order_by(EventArticle.is_seed.desc(), EventArticle.similarity.desc())
    )
    rows = (await session.execute(stmt)).all()
    out.articles = [
        EventArticleRef(
            id=r.id,
            title=r.title,
            source_id=r.source_id,
            language=r.language,
            published_at=r.published_at,
            similarity=r.similarity,
            is_seed=r.is_seed,
        )
        for r in rows
    ]
    return out
