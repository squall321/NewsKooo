"""Ranking tests: emergingness composite + rank_targets ordering.

Deterministic synthetic series, no live services. Verifies:
* an accelerating ramp ranks above a linear ramp,
* higher source diversity raises rank for otherwise-equal series,
* flat/noisy series score low.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np
from newskoo.analyze.ranking import (
    WEIGHTS,
    EmergingFeatures,
    RankItem,
    emergingness,
    extract_features,
    rank_targets,
)

_BASE = datetime(2026, 1, 5, 0, 0, tzinfo=UTC)


def _ts(n: int) -> list[datetime]:
    return [_BASE + timedelta(hours=i) for i in range(n)]


def test_weights_sum_to_one() -> None:
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def test_emergingness_is_bounded() -> None:
    strong = EmergingFeatures(
        robust_z=10.0, acceleration=10.0, burst_level=4, max_burst_level=4, source_count=50
    )
    weak = EmergingFeatures(
        robust_z=-2.0, acceleration=-5.0, burst_level=0, max_burst_level=0, source_count=0
    )
    assert 0.0 <= emergingness(weak) < emergingness(strong) <= 1.0
    assert emergingness(strong) > 0.8


def test_flat_series_scores_low() -> None:
    counts = [6] * 60
    feats = extract_features(counts, _ts(60), source_count=2)
    assert emergingness(feats) < 0.3


def test_accelerating_ramp_outranks_linear_ramp() -> None:
    n = 60
    linear = np.array([2.0 * i for i in range(n)])
    accel = np.array([0.05 * i * i for i in range(n)])  # quadratic ramp
    items = [
        RankItem(key="linear", counts=linear, timestamps=_ts(n), source_count=5),
        RankItem(key="accel", counts=accel, timestamps=_ts(n), source_count=5),
    ]
    ranked = rank_targets(items)
    assert ranked[0].key == "accel"
    accel_score = next(r.score for r in ranked if r.key == "accel")
    linear_score = next(r.score for r in ranked if r.key == "linear")
    assert accel_score > linear_score
    # Acceleration component drives the gap.
    accel_comp = next(r for r in ranked if r.key == "accel").components["acceleration"]
    linear_comp = next(r for r in ranked if r.key == "linear").components["acceleration"]
    assert accel_comp > linear_comp


def test_higher_source_diversity_raises_rank() -> None:
    # Identical spiking series; only the distinct-source count differs.
    spike = [3] * 30 + [3, 4, 5, 9, 20, 45]
    feats_low = extract_features(spike, _ts(len(spike)), source_count=1)
    feats_high = extract_features(spike, _ts(len(spike)), source_count=40)
    assert emergingness(feats_high) > emergingness(feats_low)

    items = [
        RankItem(key="few_sources", features=feats_low),
        RankItem(key="many_sources", features=feats_high),
    ]
    ranked = rank_targets(items)
    assert ranked[0].key == "many_sources"


def test_rank_targets_is_sorted_descending_and_deterministic() -> None:
    n = 50
    items = [
        RankItem(
            key=f"t{j}",
            counts=np.array([0.02 * j * i * i for i in range(n)]),
            timestamps=_ts(n),
            source_count=j,
        )
        for j in range(1, 6)
    ]
    ranked = rank_targets(items)
    scores = [r.score for r in ranked]
    assert scores == sorted(scores, reverse=True)
    # Stable: rerunning yields the same order.
    again = [r.key for r in rank_targets(items)]
    assert [r.key for r in ranked] == again


def test_components_are_reported_and_bounded() -> None:
    feats = extract_features([2] * 20 + [50, 60, 70], _ts(23), source_count=8)
    ranked = rank_targets([RankItem(key="x", features=feats)])
    comp = ranked[0].components
    assert set(comp) == set(WEIGHTS)
    assert all(0.0 <= v <= 1.0 for v in comp.values())


def test_extract_features_empty_series_is_safe() -> None:
    feats = extract_features([], [], source_count=3)
    assert feats.robust_z == 0.0
    assert feats.burst_level == 0
    assert emergingness(feats) >= 0.0
