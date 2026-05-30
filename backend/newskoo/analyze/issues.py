"""Issue-detection engine: volume/velocity anomaly detection on mentions.

Pull-based (reads from PostgreSQL) rather than consuming ``analyze.results`` —
this deliberately avoids racing the persistence stage and lets detection run on
a steady cadence over whatever is already stored.

Pipeline:

1. :meth:`IssueDetector.rebuild_timeseries` — bucket mention counts per
   ``(target_type, target_id, bucket)`` by joining article_entities /
   article_topics / article_keywords to ``articles.published_at``, and upsert
   them into ``mention_timeseries`` (count + distinct source_count).
2. velocity + z-score per series — :meth:`compute_anomalies` walks each series'
   buckets chronologically, computing ``velocity`` (Δcount per minute) and an
   EWMA-based ``zscore`` (current count vs. the exponentially-weighted mean/std
   of the preceding buckets), and writes both back to ``mention_timeseries``.
3. :meth:`detect` — for each series it derives the composite *emergingness* via
   :func:`~newskoo.analyze.ranking.extract_features` +
   :func:`~newskoo.analyze.ranking.emergingness` (a weighted blend of robust
   seasonal z-score, acceleration, Kleinberg burst level and source diversity)
   and fires an :class:`IssueAlert` when ``emergingness >=
   settings.issue_emergingness_threshold``. The alert's ``score`` is the
   emergingness; ``velocity`` is the latest smoothed first-difference. Each alert
   carries recent supporting article ids.

The persisted EWMA ``zscore`` (step 2) is retained as a secondary/diagnostic
signal — it feeds the trends API and the robust z-score component — but it is no
longer the firing gate; emergingness is. Emergingness fuses anomaly magnitude
with whether the series is *rising* (acceleration / burst) and corroborated
(distinct sources), so a sudden spike against a quiet baseline scores high while
a merely large-but-steady (or single-source) series does not.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import numpy as np
from sqlalchemy import TIMESTAMP, Interval, cast, func, literal, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from newskoo.analyze.ranking import emergingness, extract_features
from newskoo.analyze.trends import velocity as trend_velocity
from newskoo.core.config import get_settings
from newskoo.core.contracts import IssueAlert
from newskoo.core.logging import get_logger
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

log = get_logger(__name__)

# EWMA smoothing factor for the rolling mean/std baseline (lower = longer memory).
_EWMA_ALPHA = 0.3
# Minimum prior buckets before a z-score is meaningful.
_MIN_HISTORY = 3
# How many recent articles to attach to an alert as supporting evidence.
_MAX_SUPPORTING = 20
# Variance floor: mention counts are roughly Poisson, so a dead-flat baseline
# (variance 0) still has expected variance ~= its mean. Without this, a spike on
# a perfectly constant series would score zero (division by ~0 → guarded to 0)
# and never alert. The floor keeps such spikes detectable.
_MIN_STD = 1.0
# Seasonal period (in buckets) forwarded to the emergingness feature extraction.
# With the default 60-minute window this is one week of hourly buckets; a series
# shorter than two periods degrades gracefully to a flat-mean baseline.
_SEASONAL_PERIOD = 168

# (target_type, join-model, foreign-key column, label-model, label-column)
_MENTION_SOURCES = (
    ("entity", ArticleEntity, ArticleEntity.entity_id, Entity, Entity.name),
    ("topic", ArticleTopic, ArticleTopic.topic_id, Topic, Topic.label),
    ("keyword", ArticleKeyword, ArticleKeyword.keyword_id, Keyword, Keyword.term),
)


def _bucket_floor(dt: datetime, window_minutes: int) -> datetime:
    """Floor a timestamp to the start of its window bucket (UTC)."""
    dt = dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    window = timedelta(minutes=window_minutes)
    n = (dt - epoch) // window
    return epoch + n * window


@dataclass
class SeriesPoint:
    bucket: datetime
    count: int
    source_count: int = 0
    velocity: float = 0.0
    zscore: float = 0.0


@dataclass
class Series:
    target_type: str
    target_id: int
    points: list[SeriesPoint] = field(default_factory=list)

    @property
    def latest(self) -> SeriesPoint | None:
        return self.points[-1] if self.points else None


def compute_series_anomalies(
    points: list[SeriesPoint], *, window_minutes: int
) -> list[SeriesPoint]:
    """Fill ``velocity`` and ``zscore`` on each point (chronological order).

    velocity = Δcount / Δminutes between consecutive buckets. zscore compares the
    current count to an EWMA mean/std built from *preceding* buckets only, so the
    current spike isn't counted in its own baseline.
    """
    if not points:
        return points
    ordered = sorted(points, key=lambda p: p.bucket)

    ewma_mean = float(ordered[0].count)
    ewma_var = 0.0
    prev: SeriesPoint | None = None
    for i, point in enumerate(ordered):
        # Velocity from the previous bucket.
        if prev is not None:
            dt_min = max((point.bucket - prev.bucket).total_seconds() / 60.0, window_minutes)
            point.velocity = (point.count - prev.count) / dt_min
        else:
            point.velocity = 0.0

        # Z-score vs. the baseline established by earlier buckets. Floor the std
        # by sqrt(mean) (Poisson) and an absolute minimum so spikes against a
        # flat/quiet baseline still register instead of dividing by ~0.
        if i >= _MIN_HISTORY:
            std = max(float(np.sqrt(ewma_var)), float(np.sqrt(max(ewma_mean, 0.0))), _MIN_STD)
            point.zscore = (point.count - ewma_mean) / std
        else:
            point.zscore = 0.0

        # Update EWMA *after* scoring this point (baseline = strictly prior).
        delta = point.count - ewma_mean
        ewma_mean += _EWMA_ALPHA * delta
        ewma_var = (1 - _EWMA_ALPHA) * (ewma_var + _EWMA_ALPHA * delta * delta)
        prev = point
    return ordered


class IssueDetector:
    """Volume/velocity anomaly detector over ``mention_timeseries``."""

    def __init__(
        self,
        *,
        window_minutes: int | None = None,
        emergingness_threshold: float | None = None,
        zscore_threshold: float | None = None,
    ):
        settings = get_settings()
        self.window_minutes = window_minutes or settings.issue_window_minutes
        # Composite emergingness is the firing gate (see :meth:`detect`).
        self.emergingness_threshold = (
            emergingness_threshold
            if emergingness_threshold is not None
            else settings.issue_emergingness_threshold
        )
        # Retained as a secondary/diagnostic threshold (no longer the gate).
        self.zscore_threshold = (
            zscore_threshold if zscore_threshold is not None else settings.issue_zscore_threshold
        )

    # ── 1. aggregate raw mentions → buckets ─────────────────────────────────
    async def rebuild_timeseries(
        self,
        session: AsyncSession,
        *,
        window_minutes: int | None = None,
        lookback: timedelta = timedelta(days=7),
    ) -> int:
        """Recompute mention buckets over ``lookback`` and upsert them.

        Returns the number of (series, bucket) rows upserted. Counts are distinct
        articles per bucket; ``source_count`` is distinct sources.
        """
        window = window_minutes or self.window_minutes
        since = datetime.now(UTC) - lookback
        # Postgres date_bin(stride, source, origin): floor published_at to the
        # window boundary. Stride/origin are bound parameters (no SQL injection).
        bucket_expr = func.date_bin(
            cast(literal(f"{window} minutes"), Interval),
            Article.published_at,
            cast(literal("1970-01-01 00:00:00+00"), TIMESTAMP(timezone=True)),
        )

        upserted = 0
        for target_type, join_model, fk_col, _label_model, _label_col in _MENTION_SOURCES:
            stmt = (
                select(
                    fk_col.label("target_id"),
                    bucket_expr.label("bucket"),
                    func.count(func.distinct(Article.id)).label("count"),
                    func.count(func.distinct(Article.source_id)).label("source_count"),
                )
                .join(Article, Article.id == join_model.article_id)
                .where(Article.published_at.is_not(None))
                .where(Article.published_at >= since)
                .group_by(fk_col, bucket_expr)
            )
            rows = (await session.execute(stmt)).all()
            for target_id, bucket, count, source_count in rows:
                await self._upsert_bucket(
                    session,
                    target_type=target_type,
                    target_id=int(target_id),
                    bucket=bucket,
                    count=int(count),
                    source_count=int(source_count),
                )
                upserted += 1
        await session.flush()
        log.info("issues.timeseries_rebuilt", rows=upserted, window_minutes=window)
        return upserted

    @staticmethod
    async def _upsert_bucket(
        session: AsyncSession,
        *,
        target_type: str,
        target_id: int,
        bucket: datetime,
        count: int,
        source_count: int,
    ) -> None:
        stmt = pg_insert(MentionTimeseries).values(
            target_type=target_type,
            target_id=target_id,
            bucket=bucket,
            count=count,
            source_count=source_count,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["target_type", "target_id", "bucket"],
            set_={"count": stmt.excluded.count, "source_count": stmt.excluded.source_count},
        )
        await session.execute(stmt)

    # ── 2. velocity + z-score, written back ──────────────────────────────────
    async def compute_anomalies(
        self, session: AsyncSession, *, lookback: timedelta = timedelta(days=7)
    ) -> list[Series]:
        """Compute velocity + zscore for every series and persist them.

        Returns the in-memory :class:`Series` list (each with scored points) so
        :meth:`detect` can reuse it without re-querying.
        """
        series_list = await self._load_series(session, lookback=lookback)
        for series in series_list:
            compute_series_anomalies(series.points, window_minutes=self.window_minutes)
            for point in series.points:
                await session.execute(
                    MentionTimeseries.__table__.update()
                    .where(
                        (MentionTimeseries.target_type == series.target_type)
                        & (MentionTimeseries.target_id == series.target_id)
                        & (MentionTimeseries.bucket == point.bucket)
                    )
                    .values(velocity=point.velocity, zscore=point.zscore)
                )
        await session.flush()
        return series_list

    async def _load_series(
        self, session: AsyncSession, *, lookback: timedelta
    ) -> list[Series]:
        since = datetime.now(UTC) - lookback
        rows = (
            await session.execute(
                select(
                    MentionTimeseries.target_type,
                    MentionTimeseries.target_id,
                    MentionTimeseries.bucket,
                    MentionTimeseries.count,
                    MentionTimeseries.source_count,
                )
                .where(MentionTimeseries.bucket >= since)
                .order_by(
                    MentionTimeseries.target_type,
                    MentionTimeseries.target_id,
                    MentionTimeseries.bucket,
                )
            )
        ).all()

        grouped: dict[tuple[str, int], Series] = {}
        for target_type, target_id, bucket, count, source_count in rows:
            key = (target_type, int(target_id))
            series = grouped.get(key)
            if series is None:
                series = Series(target_type=target_type, target_id=int(target_id))
                grouped[key] = series
            series.points.append(
                SeriesPoint(
                    bucket=bucket,
                    count=int(count),
                    source_count=int(source_count or 0),
                )
            )
        return list(grouped.values())

    # ── 3. detect alerts ─────────────────────────────────────────────────────
    async def detect(
        self,
        session: AsyncSession,
        *,
        series: list[Series] | None = None,
    ) -> list[IssueAlert]:
        """Return :class:`IssueAlert`s for series whose emergingness clears the gate.

        For each series the full count/timestamp history (plus the latest
        bucket's distinct ``source_count``) is fed through
        :func:`~newskoo.analyze.ranking.extract_features` +
        :func:`~newskoo.analyze.ranking.emergingness`. A series fires when its
        composite emergingness reaches ``settings.issue_emergingness_threshold``;
        the alert's ``score`` is that emergingness and ``velocity`` is the latest
        smoothed first-difference (:func:`~newskoo.analyze.trends.velocity`). The
        persisted EWMA z-score is kept as a secondary signal but no longer gates.

        If ``series`` (already scored, e.g. from :meth:`compute_anomalies`) is
        not provided, the buckets are read from ``mention_timeseries`` directly.
        """
        scored = series if series is not None else await self._series_from_db(session)
        alerts: list[IssueAlert] = []
        for s in scored:
            if not s.points:
                continue

            ordered = sorted(s.points, key=lambda p: p.bucket)
            latest = ordered[-1]  # the trailing bucket — what "emerging" reads off
            counts = [p.count for p in ordered]
            timestamps = [p.bucket for p in ordered]
            # Distinct sources mentioning the target in the trailing (latest)
            # bucket — the corroboration signal at the emerging moment.
            source_count = latest.source_count

            features = extract_features(
                counts,
                timestamps,
                source_count=source_count,
                period=_SEASONAL_PERIOD,
            )
            emerging = emergingness(features)
            if emerging < self.emergingness_threshold:
                continue

            # Latest smoothed velocity (counts/bucket). Falls back to the
            # persisted per-minute velocity when the series is too short to smooth.
            vel_series = trend_velocity(counts)
            velocity = float(vel_series[-1]) if vel_series.size else latest.velocity

            label = await self._label_for(session, s.target_type, s.target_id)
            supporting = await self._supporting_articles(
                session, s.target_type, s.target_id, latest.bucket
            )
            alerts.append(
                IssueAlert(
                    target_type=s.target_type,
                    target_id=s.target_id,
                    label=label,
                    score=round(emerging, 6),
                    window_start=latest.bucket,
                    window_end=latest.bucket + timedelta(minutes=self.window_minutes),
                    mention_count=latest.count,
                    velocity=round(velocity, 4),
                    supporting_article_ids=supporting,
                )
            )
        log.info(
            "issues.detected",
            alerts=len(alerts),
            threshold=self.emergingness_threshold,
        )
        return alerts

    async def _series_from_db(self, session: AsyncSession) -> list[Series]:
        """Build scored Series straight from the persisted velocity/zscore columns."""
        rows = (
            await session.execute(
                select(
                    MentionTimeseries.target_type,
                    MentionTimeseries.target_id,
                    MentionTimeseries.bucket,
                    MentionTimeseries.count,
                    MentionTimeseries.source_count,
                    MentionTimeseries.velocity,
                    MentionTimeseries.zscore,
                ).order_by(
                    MentionTimeseries.target_type,
                    MentionTimeseries.target_id,
                    MentionTimeseries.bucket,
                )
            )
        ).all()
        grouped: dict[tuple[str, int], Series] = {}
        for target_type, target_id, bucket, count, source_count, velocity, zscore in rows:
            key = (target_type, int(target_id))
            series = grouped.get(key)
            if series is None:
                series = Series(target_type=target_type, target_id=int(target_id))
                grouped[key] = series
            series.points.append(
                SeriesPoint(
                    bucket=bucket,
                    count=int(count),
                    source_count=int(source_count or 0),
                    velocity=float(velocity or 0.0),
                    zscore=float(zscore or 0.0),
                )
            )
        return list(grouped.values())

    @staticmethod
    async def _label_for(session: AsyncSession, target_type: str, target_id: int) -> str:
        for ttype, _join, _fk, label_model, label_col in _MENTION_SOURCES:
            if ttype == target_type:
                value = await session.scalar(
                    select(label_col).where(label_model.id == target_id)
                )
                return value or f"{target_type}:{target_id}"
        return f"{target_type}:{target_id}"

    @staticmethod
    async def _supporting_articles(
        session: AsyncSession,
        target_type: str,
        target_id: int,
        bucket: datetime,
    ) -> list[int]:
        """Recent article ids mentioning the target around the spike bucket."""
        join_map = {t[0]: (t[1], t[2]) for t in _MENTION_SOURCES}
        join_model, fk_col = join_map[target_type]
        rows = (
            await session.execute(
                select(Article.id)
                .join(join_model, join_model.article_id == Article.id)
                .where(fk_col == target_id)
                .order_by(Article.published_at.desc().nullslast())
                .limit(_MAX_SUPPORTING)
            )
        ).all()
        return [int(r[0]) for r in rows]
