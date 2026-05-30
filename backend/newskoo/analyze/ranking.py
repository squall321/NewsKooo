"""Emergingness scoring: blend trend signals into one rankable score.

``emergingness`` fuses four independent signals of an emerging issue into a
single bounded score, and ``rank_targets`` applies it across many targets
(entities / topics / keywords) and sorts them, returning a per-target component
breakdown for explainability.

Signal blend
------------
Each signal is squashed into ``[0, 1]`` before weighting so no single raw scale
dominates, then combined as a weighted sum (weights sum to 1.0):

================  ======  ============================================================
component         weight  meaning
================  ======  ============================================================
robust_z          0.40    robust (median/MAD) z vs. the *seasonal* baseline — how
                          anomalous the latest residual is. The headline signal.
acceleration      0.25    smoothed 2nd difference of the series — growth that is
                          itself speeding up (an early-trend tell, not just a
                          one-off spike).
burst_level       0.20    Kleinberg burst level of the latest bucket, normalised
                          by the series' max level — sustained density, not noise.
source_diversity  0.15    distinct sources mentioning the target — many independent
                          sources corroborating beats a single noisy outlet.
================  ======  ============================================================

The weighting reflects detection priorities: anomaly magnitude leads, with
acceleration and burst confirming it is *emerging* (rising) rather than a flat
plateau, and source diversity guarding against single-source artefacts. All
weights live in :data:`WEIGHTS` and are documented inline; tune there.

Squashing
---------
* z-score → logistic ``1 / (1 + exp(-(z - z0)/scale))`` centred at ``z0`` so a
  z below the alert threshold contributes ~0 and a strong spike saturates ~1.
* acceleration → ``tanh(accel / accel_scale)`` clamped at 0 (only positive
  acceleration counts; decelerating series don't earn emergingness).
* burst level → ``level / max_level`` (0 when the series never bursts).
* source diversity → saturating ``count / (count + k)`` so the first few
  independent sources matter most and it can't run away.

``numpy`` only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

from newskoo.analyze.burst import detect_bursts
from newskoo.analyze.trends import (
    acceleration,
    seasonal_baseline,
    zscore_vs_baseline,
)

# ── blend weights (sum to 1.0) ──────────────────────────────────────────────────
WEIGHTS: dict[str, float] = {
    "robust_z": 0.40,  # anomaly magnitude vs seasonal baseline — headline signal
    "acceleration": 0.25,  # growth that is itself accelerating
    "burst_level": 0.20,  # Kleinberg burst density of the latest bucket
    "source_diversity": 0.15,  # independent-source corroboration
}

# Logistic centre/scale for the z-score squash. Centre near the default alert
# threshold so sub-threshold z's contribute little; scale controls sharpness.
_Z_CENTER = 3.0
_Z_SCALE = 1.0
# tanh scale for acceleration (counts/bucket^2); larger ⇒ needs faster ramp-up.
_ACCEL_SCALE = 2.0
# Saturation constant for source diversity: at k distinct sources the component
# is 0.5; more sources approach 1.0 with diminishing returns.
_SOURCE_K = 5.0


def _logistic(x: float, center: float, scale: float) -> float:
    """Numerically stable logistic squash to (0, 1)."""
    z = (x - center) / max(scale, 1e-9)
    # Avoid overflow in exp for large-magnitude z.
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    ez = math.exp(z)
    return ez / (1.0 + ez)


@dataclass(frozen=True)
class EmergingFeatures:
    """Pre-extracted scalar features for :func:`emergingness`.

    These are the *raw* (un-squashed) signals; :func:`emergingness` normalises
    each one. Build them yourself, or use :func:`extract_features` to derive them
    from a full series + source count.
    """

    robust_z: float  # robust z of the latest residual vs seasonal baseline
    acceleration: float  # latest smoothed second-difference
    burst_level: int  # Kleinberg burst level of the latest bucket
    max_burst_level: int  # peak burst level across the series (for normalising)
    source_count: int  # distinct sources mentioning the target


@dataclass(frozen=True)
class RankedTarget:
    """A scored target with its component breakdown, returned by :func:`rank_targets`."""

    key: object  # caller-supplied identifier (e.g. (target_type, target_id))
    score: float  # composite emergingness in [0, 1]
    components: dict[str, float]  # normalised per-signal contributions (pre-weight)
    features: EmergingFeatures


def emergingness(features: EmergingFeatures) -> float:
    """Composite emergingness score in ``[0, 1]`` (higher = more emerging).

    Blends the four normalised signals using :data:`WEIGHTS`. See the module
    docstring for the squashing of each component. Returns the weighted sum,
    which lies in ``[0, 1]`` because each normalised component does and the
    weights sum to 1.0.
    """
    components = _normalised_components(features)
    return float(sum(WEIGHTS[name] * value for name, value in components.items()))


def _normalised_components(features: EmergingFeatures) -> dict[str, float]:
    """Squash each raw feature into ``[0, 1]`` (see module docstring)."""
    z_norm = _logistic(features.robust_z, _Z_CENTER, _Z_SCALE)
    # Only positive acceleration counts toward "emerging"; clamp negatives to 0.
    accel_norm = max(0.0, math.tanh(features.acceleration / _ACCEL_SCALE))
    if features.max_burst_level > 0:
        burst_norm = max(0.0, min(1.0, features.burst_level / features.max_burst_level))
    else:
        burst_norm = 0.0
    src = max(0, features.source_count)
    source_norm = src / (src + _SOURCE_K)
    return {
        "robust_z": z_norm,
        "acceleration": accel_norm,
        "burst_level": burst_norm,
        "source_diversity": source_norm,
    }


def extract_features(
    counts: object,
    timestamps: list[datetime],
    *,
    source_count: int,
    period: int = 168,
) -> EmergingFeatures:
    """Derive :class:`EmergingFeatures` from a full series + distinct-source count.

    Runs the seasonal baseline, robust z, acceleration and burst detection over
    the whole series and reads off the *latest* bucket's values (the trailing
    edge is what "emerging" cares about). ``period`` is forwarded to
    :func:`~newskoo.analyze.trends.seasonal_baseline`.
    """
    arr = np.asarray(counts, dtype=np.float64).ravel()
    if arr.size == 0:
        return EmergingFeatures(
            robust_z=0.0,
            acceleration=0.0,
            burst_level=0,
            max_burst_level=0,
            source_count=max(0, source_count),
        )
    baseline = seasonal_baseline(arr, timestamps, period=period)
    z = zscore_vs_baseline(arr, baseline)
    accel = acceleration(arr)
    bursts = detect_bursts(arr)
    return EmergingFeatures(
        robust_z=float(z[-1]),
        acceleration=float(accel[-1]),
        burst_level=int(bursts.levels[-1]),
        max_burst_level=int(bursts.levels.max()) if bursts.levels.size else 0,
        source_count=max(0, source_count),
    )


@dataclass(frozen=True)
class RankItem:
    """Input to :func:`rank_targets`: a target's series + metadata.

    Either supply pre-computed ``features``, or supply ``counts`` (+ optional
    ``timestamps``) and ``source_count`` and let :func:`rank_targets` extract
    them.
    """

    key: object
    counts: object = None
    timestamps: list[datetime] = field(default_factory=list)
    source_count: int = 0
    features: EmergingFeatures | None = None
    period: int = 168


def rank_targets(items: list[RankItem]) -> list[RankedTarget]:
    """Score and rank targets by emergingness, descending.

    For each item, uses its pre-computed ``features`` if present, otherwise
    extracts them from ``counts``/``timestamps``/``source_count`` via
    :func:`extract_features`. Returns :class:`RankedTarget`s sorted by ``score``
    descending (ties broken by ``robust_z`` then ``source_count`` so the result
    is deterministic). Each carries the normalised component breakdown for
    explainability / UI display.
    """
    ranked: list[RankedTarget] = []
    for item in items:
        if item.features is not None:
            features = item.features
        else:
            features = extract_features(
                item.counts,
                item.timestamps,
                source_count=item.source_count,
                period=item.period,
            )
        components = _normalised_components(features)
        score = float(sum(WEIGHTS[name] * value for name, value in components.items()))
        ranked.append(
            RankedTarget(
                key=item.key,
                score=round(score, 6),
                components={name: round(v, 6) for name, v in components.items()},
                features=features,
            )
        )

    ranked.sort(
        key=lambda r: (r.score, r.features.robust_z, r.features.source_count),
        reverse=True,
    )
    return ranked


__all__ = [
    "WEIGHTS",
    "EmergingFeatures",
    "RankItem",
    "RankedTarget",
    "emergingness",
    "extract_features",
    "rank_targets",
]
