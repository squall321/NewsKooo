"""Article query endpoints: list (filtered), detail (with entities/topics),
and a recent feed.

All endpoints are read-only and open. Filters compose into a single
``select`` over the ``articles`` table; the detail view additionally loads the
M:N entity/topic links so the frontend can render context in one round-trip.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from newskoo.api.deps import SessionDep
from newskoo.api.routers import LimitQuery, OffsetQuery
from newskoo.api.schemas import (
    ArticleOut,
    EntityRef,
    Paginated,
    TopicRef,
)
from newskoo.models.article import Article
from newskoo.models.taxonomy import (
    ArticleEntity,
    ArticleTopic,
    Entity,
    Topic,
)

router = APIRouter(prefix="/articles", tags=["articles"])


def _apply_filters(
    stmt,
    *,
    source_id: int | None,
    language: str | None,
    since: datetime | None,
    until: datetime | None,
):
    if source_id is not None:
        stmt = stmt.where(Article.source_id == source_id)
    if language is not None:
        stmt = stmt.where(Article.language == language)
    if since is not None:
        stmt = stmt.where(Article.published_at >= since)
    if until is not None:
        stmt = stmt.where(Article.published_at <= until)
    return stmt


@router.get("", response_model=Paginated[ArticleOut])
async def list_articles(
    session: AsyncSession = SessionDep,
    source_id: int | None = None,
    language: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    limit: int = LimitQuery,
    offset: int = OffsetQuery,
) -> Paginated[ArticleOut]:
    stmt = select(Article).order_by(
        Article.published_at.desc().nullslast(), Article.id.desc()
    )
    stmt = _apply_filters(
        stmt, source_id=source_id, language=language, since=since, until=until
    )
    rows = (await session.execute(stmt.limit(limit).offset(offset))).scalars().all()

    count_stmt = _apply_filters(
        select(func.count()).select_from(Article),
        source_id=source_id,
        language=language,
        since=since,
        until=until,
    )
    total = int(await session.scalar(count_stmt) or 0)
    return Paginated[ArticleOut](
        items=[ArticleOut.model_validate(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/recent", response_model=list[ArticleOut])
async def recent_feed(
    session: AsyncSession = SessionDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[ArticleOut]:
    """Most recently fetched articles (ingestion feed)."""
    stmt = select(Article).order_by(Article.fetched_at.desc()).limit(limit)
    rows = (await session.execute(stmt)).scalars().all()
    return [ArticleOut.model_validate(r) for r in rows]


async def _load_entities(session: AsyncSession, article_id: int) -> list[EntityRef]:
    stmt = (
        select(
            Entity.id,
            Entity.name,
            Entity.type,
            ArticleEntity.salience,
            ArticleEntity.sentiment,
        )
        .join(ArticleEntity, ArticleEntity.entity_id == Entity.id)
        .where(ArticleEntity.article_id == article_id)
        .order_by(ArticleEntity.salience.desc())
    )
    rows = (await session.execute(stmt)).all()
    return [
        EntityRef(id=r.id, name=r.name, type=r.type, salience=r.salience, sentiment=r.sentiment)
        for r in rows
    ]


async def _load_topics(session: AsyncSession, article_id: int) -> list[TopicRef]:
    stmt = (
        select(Topic.id, Topic.slug, Topic.label, ArticleTopic.confidence)
        .join(ArticleTopic, ArticleTopic.topic_id == Topic.id)
        .where(ArticleTopic.article_id == article_id)
        .order_by(ArticleTopic.confidence.desc())
    )
    rows = (await session.execute(stmt)).all()
    return [
        TopicRef(id=r.id, slug=r.slug, label=r.label, confidence=r.confidence)
        for r in rows
    ]


@router.get("/{article_id}", response_model=ArticleOut)
async def get_article(
    article_id: int, session: AsyncSession = SessionDep
) -> ArticleOut:
    art = await session.get(Article, article_id)
    if art is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "article not found")
    out = ArticleOut.model_validate(art)
    out.entities = await _load_entities(session, article_id)
    out.topics = await _load_topics(session, article_id)
    return out
