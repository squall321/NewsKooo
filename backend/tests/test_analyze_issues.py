"""Issue-detection tests: synthetic series → spike yields an alert, flat none.

These test the windowing + z-score math (``compute_series_anomalies``) directly,
and ``IssueDetector.detect`` against a fake session whose label / supporting-id
queries return canned values. No database.

``detect`` no longer fires on the latest EWMA z-score; it scores each series'
composite *emergingness* (``analyze.ranking.extract_features`` +
``emergingness``) and fires when that clears ``issue_emergingness_threshold``.
The alert's ``score`` is the emergingness itself, so the tests recompute it the
same way and assert equality.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from newskoo.analyze.issues import IssueDetector, Series, SeriesPoint, compute_series_anomalies
from newskoo.analyze.ranking import emergingness, extract_features
from newskoo.core.contracts import IssueAlert

_WINDOW = 60
_BASE = datetime(2026, 5, 29, 0, 0, tzinfo=UTC)


def _series(
    counts: list[int],
    *,
    target_type: str = "entity",
    target_id: int = 42,
    source_count: int = 0,
) -> Series:
    points = [
        SeriesPoint(
            bucket=_BASE + timedelta(minutes=_WINDOW * i),
            count=c,
            source_count=source_count,
        )
        for i, c in enumerate(counts)
    ]
    return Series(target_type=target_type, target_id=target_id, points=points)


def _expected_emergingness(counts: list[int], *, source_count: int) -> float:
    """Recompute the composite emergingness the way ``detect`` does."""
    features = extract_features(
        counts,
        [_BASE + timedelta(minutes=_WINDOW * i) for i in range(len(counts))],
        source_count=source_count,
        period=168,
    )
    return round(emergingness(features), 6)


# ── pure math ────────────────────────────────────────────────────────────────


def test_spike_series_scores_high_zscore() -> None:
    # Quiet baseline then a sharp jump.
    points = _series([2, 3, 2, 3, 2, 50]).points
    compute_series_anomalies(points, window_minutes=_WINDOW)
    latest = points[-1]
    assert latest.zscore > 3.0
    assert latest.velocity > 0  # count climbed from the prior bucket


def test_flat_series_scores_low_zscore() -> None:
    points = _series([5, 5, 5, 5, 5, 5]).points
    compute_series_anomalies(points, window_minutes=_WINDOW)
    assert abs(points[-1].zscore) < 1.0


def test_short_series_has_zero_zscore() -> None:
    # Below the minimum history, no z-score is computed.
    points = _series([1, 100]).points
    compute_series_anomalies(points, window_minutes=_WINDOW)
    assert all(p.zscore == 0.0 for p in points)


# ── detect() against a fake session ───────────────────────────────────────────


class _FakeScalarResult:
    def __init__(self, rows: list[tuple[Any, ...]]) -> None:
        self._rows = rows

    def all(self) -> list[tuple[Any, ...]]:
        return self._rows


class FakeSession:
    """Minimal AsyncSession stand-in for detect(): scalar() → label, execute() → ids."""

    def __init__(self, *, label: str, supporting_ids: list[int]) -> None:
        self._label = label
        self._supporting_ids = supporting_ids

    async def scalar(self, _stmt: Any) -> str:
        return self._label

    async def execute(self, _stmt: Any) -> _FakeScalarResult:
        return _FakeScalarResult([(i,) for i in self._supporting_ids])


async def test_detect_emits_alert_above_threshold() -> None:
    # A clear spike fires via emergingness (well above the default 0.6 gate).
    detector = IssueDetector(window_minutes=_WINDOW, emergingness_threshold=0.6)
    counts = [2, 3, 2, 3, 2, 50]
    spike = _series(counts, target_id=7, source_count=4)
    compute_series_anomalies(spike.points, window_minutes=_WINDOW)

    session = FakeSession(label="Acme Corp", supporting_ids=[101, 102])
    alerts = await detector.detect(session, series=[spike])  # type: ignore[arg-type]

    assert len(alerts) == 1
    alert = alerts[0]
    assert isinstance(alert, IssueAlert)
    assert alert.target_type == "entity"
    assert alert.target_id == 7
    assert alert.label == "Acme Corp"
    # score is the composite emergingness, not the z-score.
    expected = _expected_emergingness(counts, source_count=4)
    assert alert.score == expected
    assert alert.score >= 0.6
    assert alert.mention_count == 50
    assert alert.velocity > 0  # series climbed into the spike
    assert alert.supporting_article_ids == [101, 102]
    assert alert.window_end - alert.window_start == timedelta(minutes=_WINDOW)


async def test_detect_skips_flat_series() -> None:
    # A flat / seasonally-normal series stays well below the emergingness gate.
    detector = IssueDetector(window_minutes=_WINDOW, emergingness_threshold=0.6)
    flat = _series([5, 5, 5, 5, 5, 5], source_count=3)
    compute_series_anomalies(flat.points, window_minutes=_WINDOW)

    assert _expected_emergingness([5, 5, 5, 5, 5, 5], source_count=3) < 0.6
    session = FakeSession(label="Quiet Topic", supporting_ids=[])
    alerts = await detector.detect(session, series=[flat])  # type: ignore[arg-type]
    assert alerts == []


async def test_detect_mixed_returns_only_spikes() -> None:
    detector = IssueDetector(window_minutes=_WINDOW, emergingness_threshold=0.6)
    spike = _series([1, 1, 1, 1, 1, 40], target_id=1, source_count=6)
    flat = _series([10, 10, 10, 10, 10, 10], target_id=2, source_count=3)
    for s in (spike, flat):
        compute_series_anomalies(s.points, window_minutes=_WINDOW)

    session = FakeSession(label="L", supporting_ids=[1])
    alerts = await detector.detect(session, series=[spike, flat])  # type: ignore[arg-type]
    assert [a.target_id for a in alerts] == [1]


def test_detector_defaults_from_settings() -> None:
    detector = IssueDetector()
    assert detector.window_minutes > 0
    assert detector.emergingness_threshold > 0
    # z-score threshold is retained as a secondary/diagnostic signal.
    assert detector.zscore_threshold > 0


@pytest.mark.parametrize("empty", [[], [SeriesPoint(bucket=_BASE, count=3)]])
def test_compute_handles_trivial_series(empty: list[SeriesPoint]) -> None:
    # Should not raise on empty or single-point series.
    out = compute_series_anomalies(empty, window_minutes=_WINDOW)
    assert len(out) == len(empty)
