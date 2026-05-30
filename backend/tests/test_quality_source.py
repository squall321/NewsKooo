"""Source-credibility tests: bounds, monotonicity, and the DB aggregation path.

Pure functions on synthetic :class:`SourceFeatures`; the async path runs against
a mocked :class:`AsyncSession` returning canned aggregate rows + source objects.
No live DB / network.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from newskoo.models.source import Source
from newskoo.quality.source_score import (
    WEIGHTS,
    SourceFeatures,
    compute_source_scores,
    credibility_components,
    source_credibility,
)

_GOOD = SourceFeatures(
    success_rate=0.99,
    error_rate=0.01,
    age_days=2000.0,
    article_count=5000,
    corroboration_rate=0.9,
)
_BAD = SourceFeatures(
    success_rate=0.2,
    error_rate=0.8,
    age_days=3.0,
    article_count=2,
    corroboration_rate=0.0,
)


def test_weights_sum_to_one() -> None:
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def test_bounded_and_good_beats_bad() -> None:
    assert 0.0 <= source_credibility(_BAD) <= 1.0
    assert 0.0 <= source_credibility(_GOOD) <= 1.0
    assert source_credibility(_GOOD) > 0.8
    assert source_credibility(_BAD) < 0.25
    assert source_credibility(_GOOD) > source_credibility(_BAD)


def test_monotonic_in_success_rate() -> None:
    base = replace(_BAD, success_rate=0.5, error_rate=0.5)
    prev = -1.0
    for sr in (0.0, 0.25, 0.5, 0.75, 1.0):
        score = source_credibility(replace(base, success_rate=sr))
        assert score >= prev - 1e-12
        prev = score


def test_monotonic_in_corroboration() -> None:
    prev = -1.0
    for corr in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
        score = source_credibility(replace(_BAD, corroboration_rate=corr))
        assert score >= prev - 1e-12
        prev = score


def test_monotonic_in_volume() -> None:
    prev = -1.0
    for vol in (0, 1, 10, 100, 1000, 100_000):
        score = source_credibility(replace(_BAD, article_count=vol))
        assert score >= prev - 1e-12
        prev = score


def test_monotonic_in_longevity() -> None:
    prev = -1.0
    for age in (0.0, 30.0, 365.0, 730.0, 3650.0):
        score = source_credibility(replace(_BAD, age_days=age))
        assert score >= prev - 1e-12
        prev = score


def test_higher_error_rate_never_raises_score() -> None:
    # error_rate appears in two (good-oriented) terms; raising it must not help.
    prev = 2.0
    for err in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0):
        feats = replace(_GOOD, error_rate=err, success_rate=1.0 - err)
        score = source_credibility(feats)
        assert score <= prev + 1e-12
        prev = score


def test_components_reported_and_bounded() -> None:
    comps = credibility_components(_GOOD)
    assert set(comps) == set(WEIGHTS)
    assert all(0.0 <= v <= 1.0 for v in comps.values())


# ── async DB path against a mocked session ──────────────────────────────────────


def _mock_session(
    sources: list[Source],
    volume_rows: list[tuple[int, int]],
    corroborated_rows: list[tuple[int, int]],
) -> AsyncMock:
    """Mock AsyncSession.

    ``execute`` is dispatched by call order: (1) volume aggregate → ``.all()``,
    (2) corroboration aggregate → ``.all()``, (3) source select →
    ``.scalars().all()``. ``flush`` is a no-op.
    """
    session = AsyncMock()

    volume_res = MagicMock()
    volume_res.all.return_value = volume_rows
    corr_res = MagicMock()
    corr_res.all.return_value = corroborated_rows
    sources_res = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = sources
    sources_res.scalars.return_value = scalars

    session.execute = AsyncMock(side_effect=[volume_res, corr_res, sources_res])
    session.flush = AsyncMock()
    return session


async def test_compute_source_scores_merges_health_without_clobber() -> None:
    now = datetime.now(UTC)
    healthy = Source(
        id=1,
        name="Reliable Wire",
        homepage_url="https://reliable.example",
        fetch_method="rss",
        health={"total": 100, "fails": 1, "error_rate": 0.01, "last_ok_at": "x"},
    )
    healthy.created_at = now - timedelta(days=1800)
    flaky = Source(
        id=2,
        name="Flaky Blog",
        homepage_url="https://flaky.example",
        fetch_method="html",
        health={"total": 50, "fails": 40, "error_rate": 0.8},
    )
    flaky.created_at = now - timedelta(days=10)

    session = _mock_session(
        sources=[healthy, flaky],
        volume_rows=[(1, 4000), (2, 5)],
        corroborated_rows=[(1, 3600)],  # flaky has no corroborated articles
    )

    scores = await compute_source_scores(session)

    assert set(scores) == {1, 2}
    assert scores[1] > scores[2]
    assert scores[1] > 0.7
    assert scores[2] < 0.3
    # Merged, not clobbered.
    assert healthy.health["credibility"] == round(scores[1], 6)
    assert "credibility_at" in healthy.health
    assert healthy.health["last_ok_at"] == "x"  # untouched
    assert healthy.health["total"] == 100
    session.flush.assert_awaited()


async def test_compute_source_scores_handles_no_history() -> None:
    now = datetime.now(UTC)
    fresh = Source(
        id=7,
        name="Brand New",
        homepage_url="https://new.example",
        fetch_method="rss",
        health={},
    )
    fresh.created_at = now

    session = _mock_session(sources=[fresh], volume_rows=[], corroborated_rows=[])
    scores = await compute_source_scores(session)

    # No fetches, no articles, no age ⇒ a low but valid score.
    assert 0.0 <= scores[7] <= 0.3
    assert fresh.health["credibility"] == round(scores[7], 6)
