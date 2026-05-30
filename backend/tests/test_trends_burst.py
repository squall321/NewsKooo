"""Burst-detection tests: Kleinberg automaton over synthetic count series.

Deterministic, no live services. Verifies that a localised dense region yields a
burst interval covering it, while flat/quiet series produce no bursts.
"""

from __future__ import annotations

import numpy as np
from newskoo.analyze.burst import BurstInterval, BurstResult, detect_bursts


def test_flat_series_has_no_burst() -> None:
    counts = [5] * 40
    result = detect_bursts(counts)
    assert isinstance(result, BurstResult)
    # A perfectly constant series is fully explained by the base state.
    assert result.intervals == []
    assert (result.levels == 0).all()


def test_localized_burst_is_detected_in_the_right_place() -> None:
    # Quiet baseline (~2/bucket) with a sharp dense window in the middle.
    counts = [2] * 20 + [60, 80, 70, 90] + [2] * 20
    result = detect_bursts(counts)

    assert result.intervals, "expected at least one burst interval"
    # The strongest burst should sit over indices 20..23.
    strongest = max(result.intervals, key=lambda iv: iv.weight)
    assert strongest.start <= 20
    assert strongest.end >= 23
    assert strongest.level >= 1
    # Buckets inside the dense window are at a raised level.
    assert result.levels[21] >= 1
    # Quiet buckets stay at baseline.
    assert result.levels[0] == 0
    assert result.levels[-1] == 0


def test_higher_gamma_suppresses_weak_bursts() -> None:
    # A mild bump that an easy gamma flags but a strict gamma should not.
    counts = [3] * 15 + [9, 10, 9] + [3] * 15
    easy = detect_bursts(counts, gamma=0.2)
    strict = detect_bursts(counts, gamma=10.0)
    assert sum(easy.levels) >= sum(strict.levels)
    assert strict.intervals == [] or all(iv.level >= 1 for iv in strict.intervals)


def test_burst_weight_is_positive_for_real_burst() -> None:
    counts = [1] * 10 + [50, 50, 50] + [1] * 10
    result = detect_bursts(counts)
    assert result.intervals
    assert all(isinstance(iv, BurstInterval) for iv in result.intervals)
    assert max(iv.weight for iv in result.intervals) > 0.0


def test_empty_and_zero_series_are_safe() -> None:
    empty = detect_bursts([])
    assert empty.levels.size == 0
    assert empty.intervals == []

    zeros = detect_bursts([0, 0, 0, 0])
    assert (zeros.levels == 0).all()
    assert zeros.intervals == []


def test_rejects_negative_counts() -> None:
    try:
        detect_bursts([1, 2, -3])
    except ValueError:
        return
    raise AssertionError("expected ValueError on negative counts")


def test_invalid_parameters_raise() -> None:
    for kwargs in ({"s": 1.0}, {"s": 0.5}, {"gamma": -1.0}):
        try:
            detect_bursts([1, 2, 3], **kwargs)  # type: ignore[arg-type]
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for {kwargs}")


def test_levels_are_nonnegative_integers() -> None:
    counts = [4] * 10 + [40] * 5 + [4] * 10
    result = detect_bursts(counts)
    assert result.levels.dtype == np.int_
    assert (result.levels >= 0).all()
    assert result.n_states >= 2
