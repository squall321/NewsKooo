"""Issue (emerging-alert) endpoints.

Issues are *derived* on read from ``mention_timeseries``: the latest bucket per
target whose ``zscore`` clears ``settings.issue_zscore_threshold`` is an alert.
Labels come from the entity/topic/keyword catalog and supporting article ids are
pulled from the relevant article↔target link table around the spike bucket.

This mirrors :class:`newskoo.analyze.issues.IssueDetector.detect` but reads the
already-persisted velocity/zscore columns (no recompute) so the API stays cheap.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from newskoo.api.deps import SessionDep
from newskoo.api.schemas import IssueOut
from newskoo.core.config import get_settings
from newskoo.models.article import Article
from newskoo.models.taxonomy import (
    ArticleEntity,
    ArticleKeyword,
    ArticleTopic,
    Entity,
    Keyword,
    Topic,
)
from newskoo.models.timeseries import MentionTimeseries

router = APIRouter(prefix="/issues", tags=["issues"])

_MAX_SUPPORTING = 20

# target_type -> (link-model, link-fk-col, label-model, label-col)
_TARGET_MAP = {
    "entity": (ArticleEntity, ArticleEntity.entity_id, Entity, Entity.name),
    "topic": (ArticleTopic, ArticleTopic.topic_id, Topic, Topic.label),
    "keyword": (ArticleKeyword, ArticleKeyword.keyword_id, Keyword, Keyword.term),
}


def _latest_bucket_subquery(since: datetime) -> Select:
    return (
        select(
            MentionTimeseries.target_type.label("tt"),
            MentionTimeseries.target_id.label("tid"),
            func.max(MentionTimeseries.bucket).label("max_bucket"),
        )
        .where(MentionTimeseries.bucket >= since)
        .group_by(MentionTimeseries.target_type, MentionTimeseries.target_id)
        .subquery()
    )


async def _label_for(session: AsyncSession, target_type: str, target_id: int) -> str:
    entry = _TARGET_MAP.get(target_type)
    if entry is None:
        return f"{target_type}:{target_id}"
    _link, _fk, label_model, label_col = entry
    value = await session.scalar(select(label_col).where(label_model.id == target_id))
    return value or f"{target_type}:{target_id}"


async def _supporting_articles(
    session: AsyncSession, target_type: str, target_id: int
) -> list[int]:
    entry = _TARGET_MAP.get(target_type)
    if entry is None:
        return []
    link_model, fk_col, _lm, _lc = entry
    rows = (
        await session.execute(
            select(Article.id)
            .join(link_model, link_model.article_id == Article.id)
            .where(fk_col == target_id)
            .order_by(Article.published_at.desc().nullslast())
            .limit(_MAX_SUPPORTING)
        )
    ).all()
    return [int(r[0]) for r in rows]


async def _build_issue(
    session: AsyncSession, row, window_minutes: int
) -> IssueOut:
    label = await _label_for(session, row.target_type, row.target_id)
    supporting = await _supporting_articles(session, row.target_type, row.target_id)
    return IssueOut(
        target_type=row.target_type,
        target_id=row.target_id,
        label=label,
        score=round(float(row.zscore or 0.0), 4),
        window_start=row.bucket,
        window_end=row.bucket + timedelta(minutes=window_minutes),
        mention_count=int(row.count),
        velocity=round(float(row.velocity or 0.0), 4),
        supporting_article_ids=supporting,
    )


@router.get("", response_model=list[IssueOut])
async def list_issues(
    session: AsyncSession = SessionDep,
    threshold: Annotated[
        float | None, Query(description="override zscore threshold")
    ] = None,
    window: Annotated[
        int, Query(ge=1, le=24 * 365, description="lookback hours")
    ] = 24,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[IssueOut]:
    settings = get_settings()
    zmin = threshold if threshold is not None else settings.issue_zscore_threshold
    since = datetime.now(UTC) - timedelta(hours=window)
    latest = _latest_bucket_subquery(since)

    stmt = (
        select(
            MentionTimeseries.target_type,
            MentionTimeseries.target_id,
            MentionTimeseries.bucket,
            MentionTimeseries.count,
            MentionTimeseries.velocity,
            MentionTimeseries.zscore,
        )
        .join(
            latest,
            (MentionTimeseries.target_type == latest.c.tt)
            & (MentionTimeseries.target_id == latest.c.tid)
            & (MentionTimeseries.bucket == latest.c.max_bucket),
        )
        .where(MentionTimeseries.zscore >= zmin)
        .order_by(MentionTimeseries.zscore.desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [
        await _build_issue(session, r, settings.issue_window_minutes) for r in rows
    ]


@router.get("/{target}", response_model=list[IssueOut])
async def issues_for_target(
    target: str,
    session: AsyncSession = SessionDep,
    window: Annotated[
        int, Query(ge=1, le=24 * 365, description="lookback hours")
    ] = 168,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[IssueOut]:
    """All spiking buckets for one ``target`` in ``type:id`` form (e.g. ``entity:42``).

    Returns every above-threshold bucket in the window (a history of the spike),
    most recent first.
    """
    try:
        target_type, target_id_str = target.split(":", 1)
        target_id = int(target_id_str)
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "target must be of the form '<type>:<id>' (e.g. entity:42)",
        ) from exc
    if target_type not in _TARGET_MAP:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"unknown target type {target_type!r}",
        )

    settings = get_settings()
    since = datetime.now(UTC) - timedelta(hours=window)
    stmt = (
        select(
            MentionTimeseries.target_type,
            MentionTimeseries.target_id,
            MentionTimeseries.bucket,
            MentionTimeseries.count,
            MentionTimeseries.velocity,
            MentionTimeseries.zscore,
        )
        .where(MentionTimeseries.target_type == target_type)
        .where(MentionTimeseries.target_id == target_id)
        .where(MentionTimeseries.bucket >= since)
        .where(MentionTimeseries.zscore >= settings.issue_zscore_threshold)
        .order_by(MentionTimeseries.bucket.desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [
        await _build_issue(session, r, settings.issue_window_minutes) for r in rows
    ]
