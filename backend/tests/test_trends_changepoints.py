"""Trend tests: seasonal baseline, robust z, CUSUM/BOCPD changepoints, velocity.

Deterministic synthetic series, no live services.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np
from newskoo.analyze.trends import (
    acceleration,
    changepoints,
    seasonal_baseline,
    velocity,
    zscore_vs_baseline,
)

_BASE = datetime(2026, 1, 5, 0, 0, tzinfo=UTC)  # a Monday 00:00


def _hourly_timestamps(n: int) -> list[datetime]:
    return [_BASE + timedelta(hours=i) for i in range(n)]


# ── CUSUM changepoints ──────────────────────────────────────────────────────────


def test_flat_noisy_series_has_no_changepoint() -> None:
    rng = np.random.default_rng(0)
    series = 10 + rng.normal(0.0, 0.5, size=200)
    result = changepoints(series, k=0.5, h=5.0)
    assert result.indices == []


def test_step_up_series_flags_changepoint_near_the_step() -> None:
    # 100 buckets at ~5, then a persistent jump to ~25.
    rng = np.random.default_rng(1)
    low = 5 + rng.normal(0.0, 0.3, size=100)
    high = 25 + rng.normal(0.0, 0.3, size=100)
    series = np.concatenate([low, high])
    result = changepoints(series, k=0.5, h=5.0)

    assert result.indices, "expected a CUSUM alarm after the step"
    first = result.indices[0]
    # CUSUM accumulates, so it fires a little after the true step (index 100),
    # but should be in its near neighbourhood — not in the flat first half.
    assert 100 <= first <= 130


def test_step_down_is_detected_by_two_sided_cusum() -> None:
    rng = np.random.default_rng(2)
    high = 30 + rng.normal(0.0, 0.3, size=80)
    low = 5 + rng.normal(0.0, 0.3, size=80)
    series = np.concatenate([high, low])
    result = changepoints(series, k=0.5, h=5.0)
    assert any(80 <= i <= 110 for i in result.indices)


def test_bocpd_probability_peaks_near_the_step() -> None:
    rng = np.random.default_rng(3)
    low = 5 + rng.normal(0.0, 0.3, size=60)
    high = 25 + rng.normal(0.0, 0.3, size=60)
    series = np.concatenate([low, high])
    result = changepoints(series, bocpd=True)
    assert result.bocpd_prob.size == series.size
    assert (result.bocpd_prob >= 0).all() and (result.bocpd_prob <= 1).all()
    # The biggest changepoint mass should land right around the regime change.
    peak = int(np.argmax(result.bocpd_prob[55:75])) + 55
    assert 58 <= peak <= 72


def test_changepoints_empty_series_is_safe() -> None:
    result = changepoints([])
    assert result.indices == []
    assert result.cusum_pos.size == 0
    assert result.bocpd_prob.size == 0


# ── velocity / acceleration ─────────────────────────────────────────────────────


def test_velocity_positive_on_rising_series() -> None:
    series = list(range(0, 50, 2))  # steadily increasing
    vel = velocity(series)
    assert vel.size == len(series)
    assert vel[0] == 0.0
    assert np.mean(vel[1:]) > 0


def test_acceleration_positive_on_accelerating_ramp() -> None:
    series = np.array([i * i for i in range(30)], dtype=float)  # quadratic ⇒ +accel
    accel = acceleration(series)
    assert accel.size == series.size
    assert np.mean(accel[2:]) > 0


def test_acceleration_near_zero_on_linear_ramp() -> None:
    series = np.array([3.0 * i for i in range(40)])  # linear ⇒ ~0 accel
    accel = acceleration(series)
    assert abs(float(np.mean(accel[2:]))) < 0.5


# ── seasonal baseline + robust z ─────────────────────────────────────────────────


def test_short_series_falls_back_to_mean_baseline() -> None:
    counts = [5, 7, 6, 5]
    ts = _hourly_timestamps(len(counts))
    baseline = seasonal_baseline(counts, ts, period=168)
    assert baseline.seasonal is False
    assert np.allclose(baseline.expected, np.mean(counts))


def test_weekly_seasonal_monday_spike_is_removed_but_off_profile_spike_kept() -> None:
    # Three weeks of hourly data (504 buckets). Baseline ~5, but every Monday
    # 09:00 has a recurring spike to ~50 (a routine weekly pattern).
    weeks = 3
    n = weeks * 168
    ts = _hourly_timestamps(n)
    counts = np.full(n, 5.0)
    for i, t in enumerate(ts):
        if t.weekday() == 0 and t.hour == 9:  # Monday 09:00 recurring spike
            counts[i] = 50.0

    baseline = seasonal_baseline(counts, ts, period=168)
    assert baseline.seasonal is True
    z = zscore_vs_baseline(counts, baseline)

    # Indices of the recurring Monday-09:00 spikes.
    monday_idx = [i for i, t in enumerate(ts) if t.weekday() == 0 and t.hour == 9]
    # A *normal* recurring Monday spike is explained by the seasonal profile, so
    # its residual z is small.
    for i in monday_idx:
        assert abs(z[i]) < 3.0, f"recurring Monday spike at {i} should not be flagged"

    # Now inject an *off-profile* spike on a Wednesday afternoon and re-baseline.
    odd = next(i for i, t in enumerate(ts) if t.weekday() == 2 and t.hour == 15)
    counts2 = counts.copy()
    counts2[odd] = 60.0
    baseline2 = seasonal_baseline(counts2, ts, period=168)
    z2 = zscore_vs_baseline(counts2, baseline2)
    assert z2[odd] > 3.0, "an off-profile spike must still be flagged"


def test_zscore_flat_series_is_near_zero() -> None:
    counts = [8] * 200
    ts = _hourly_timestamps(len(counts))
    baseline = seasonal_baseline(counts, ts, period=168)
    z = zscore_vs_baseline(counts, baseline)
    assert np.all(np.abs(z) < 1e-6)


def test_seasonal_timestamp_length_mismatch_raises() -> None:
    try:
        seasonal_baseline([1, 2, 3], _hourly_timestamps(2), period=168)
    except ValueError:
        return
    raise AssertionError("expected ValueError on length mismatch")
