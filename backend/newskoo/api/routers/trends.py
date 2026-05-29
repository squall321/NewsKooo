"""Trend endpoints over ``mention_timeseries``.

``GET /trends`` returns the bucketed series (count / velocity / zscore) for one
target. A target is addressed either directly by ``target_type`` + ``target_id``
or, for convenience, by ``target_type`` + ``keyword`` label which is resolved to
an id against the entity/topic/keyword catalog.

``GET /trends/top`` returns the targets whose *latest* bucket has the highest
velocity or z-score — i.e. what is accelerating right now — joined to labels.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from newskoo.api.deps import SessionDep
from newskoo.api.schemas import TrendPoint, TrendSeries
from newskoo.models.taxonomy import Entity, Keyword, Topic
from newskoo.models.timeseries import MentionTimeseries

router = APIRouter(prefix="/trends", tags=["trends"])


class TargetType(StrEnum):
    ENTITY = "entity"
    TOPIC = "topic"
    KEYWORD = "keyword"


class TopMetric(StrEnum):
    VELOCITY = "velocity"
    ZSCORE = "zscore"


# (label-model, label-column) per target type — for resolving + labelling.
_LABEL_MAP = {
    TargetType.ENTITY: (Entity, Entity.name),
    TargetType.TOPIC: (Topic, Topic.label),
    TargetType.KEYWORD: (Keyword, Keyword.term),
}


async def _resolve_keyword(
    session: AsyncSession, target_type: TargetType, keyword: str
) -> int | None:
    """Resolve a human label to a catalog id for the given target type."""
    label_model, label_col = _LABEL_MAP[target_type]
    return await session.scalar(
        select(label_model.id).where(func.lower(label_col) == keyword.lower()).limit(1)
    )


async def _label_for(
    session: AsyncSession, target_type: TargetType, target_id: int
) -> str:
    label_model, label_col = _LABEL_MAP[target_type]
    value = await session.scalar(select(label_col).where(label_model.id == target_id))
    return value or f"{target_type.value}:{target_id}"


@router.get("", response_model=TrendSeries)
async def get_trend(
    session: AsyncSession = SessionDep,
    target_type: TargetType = Query(...),  # noqa: B008  (FastAPI required query param)
    target_id: int | None = None,
    keyword: Annotated[
        str | None, Query(description="label to resolve to an id")
    ] = None,
    window: Annotated[
        int, Query(ge=1, le=24 * 365, description="lookback hours")
    ] = 168,
) -> TrendSeries:
    if target_id is None:
        if not keyword:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "provide either target_id or keyword",
            )
        target_id = await _resolve_keyword(session, target_type, keyword)
        if target_id is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "target not found")

    since = datetime.now(UTC) - timedelta(hours=window)
    stmt = (
        select(
            MentionTimeseries.bucket,
            MentionTimeseries.count,
            MentionTimeseries.source_count,
            MentionTimeseries.velocity,
            MentionTimeseries.zscore,
        )
        .where(MentionTimeseries.target_type == target_type.value)
        .where(MentionTimeseries.target_id == target_id)
        .where(MentionTimeseries.bucket >= since)
        .order_by(MentionTimeseries.bucket)
    )
    rows = (await session.execute(stmt)).all()
    label = await _label_for(session, target_type, target_id)
    return TrendSeries(
        target_type=target_type.value,
        target_id=target_id,
        label=label,
        points=[
            TrendPoint(
                bucket=r.bucket,
                count=r.count,
                source_count=r.source_count,
                velocity=r.velocity,
                zscore=r.zscore,
            )
            for r in rows
        ],
    )


def _latest_bucket_subquery(since: datetime) -> Select:
    """Per-target latest bucket within the window (for 'what's hot now')."""
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


@router.get("/top", response_model=list[TrendSeries])
async def top_trends(
    session: AsyncSession = SessionDep,
    metric: TopMetric = TopMetric.ZSCORE,
    target_type: TargetType | None = None,
    window: Annotated[
        int, Query(ge=1, le=24 * 365, description="lookback hours")
    ] = 24,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[TrendSeries]:
    """Targets with the highest latest-bucket velocity/zscore in the window."""
    since = datetime.now(UTC) - timedelta(hours=window)
    latest = _latest_bucket_subquery(since)
    metric_col = (
        MentionTimeseries.velocity
        if metric == TopMetric.VELOCITY
        else MentionTimeseries.zscore
    )
    stmt = (
        select(
            MentionTimeseries.target_type,
            MentionTimeseries.target_id,
            MentionTimeseries.bucket,
            MentionTimeseries.count,
            MentionTimeseries.source_count,
            MentionTimeseries.velocity,
            MentionTimeseries.zscore,
        )
        .join(
            latest,
            (MentionTimeseries.target_type == latest.c.tt)
            & (MentionTimeseries.target_id == latest.c.tid)
            & (MentionTimeseries.bucket == latest.c.max_bucket),
        )
        .order_by(metric_col.desc())
        .limit(limit)
    )
    if target_type is not None:
        stmt = stmt.where(MentionTimeseries.target_type == target_type.value)

    rows = (await session.execute(stmt)).all()
    out: list[TrendSeries] = []
    for r in rows:
        tt = TargetType(r.target_type)
        label = await _label_for(session, tt, r.target_id)
        out.append(
            TrendSeries(
                target_type=r.target_type,
                target_id=r.target_id,
                label=label,
                points=[
                    TrendPoint(
                        bucket=r.bucket,
                        count=r.count,
                        source_count=r.source_count,
                        velocity=r.velocity,
                        zscore=r.zscore,
                    )
                ],
            )
        )
    return out
