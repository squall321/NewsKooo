"""Advanced trend detection: seasonal baselines, robust z-scores, changepoints.

These functions operate on plain numpy count series (e.g. the per-bucket
``count`` column of :class:`~newskoo.models.timeseries.MentionTimeseries`) and
are deliberately free of any DB / async coupling so they can be unit-tested with
synthetic series and composed by the issues worker.

Algorithms & references
------------------------
* **Seasonal baseline** — a multiplicative day-of-week x hour-of-day profile,
  the classic decomposition ``observed = trend * seasonal * residual`` used in
  STL / classical seasonal decomposition (Cleveland et al. 1990). We estimate
  the seasonal index for each (dow, hour) slot as the mean ratio of observed to
  the overall mean, then deseasonalise by dividing it out.
* **Robust z-score** — median / MAD based standard score (Iglewicz & Hoaglin,
  "How to Detect and Handle Outliers", 1993). The 0.6745 constant makes MAD a
  consistent estimator of the standard deviation for normal data.
* **CUSUM changepoint** — Page's two-sided cumulative-sum control chart
  (E. S. Page, "Continuous Inspection Schemes", Biometrika 1954). Detects a
  persistent shift in mean, online, with a slack ``k`` and alarm threshold ``h``.
* **Bayesian online changepoint** — run-length posterior of Adams & MacKay,
  "Bayesian Online Changepoint Detection" (2007), with a Gaussian observation
  model and constant hazard. Used to emit a per-bucket changepoint probability.
* **Velocity / acceleration** — smoothed first and second finite differences.

``numpy`` only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
from numpy.typing import NDArray

# MAD → sigma scaling for normally distributed data (Iglewicz & Hoaglin 1993).
_MAD_TO_SIGMA = 0.6745
# Floor for any scale estimate so robust z-scores never divide by ~0.
_MIN_SCALE = 1e-9
# Minimum observations in a seasonal slot before we trust its index; below this
# the slot falls back to the global mean (index 1.0).
_MIN_SLOT_OBS = 2
# A series shorter than this (relative to the seasonal period) can't support a
# seasonal estimate, so ``seasonal_baseline`` falls back to a flat mean.
_MIN_PERIODS_FOR_SEASONAL = 2
# Default smoothing window (buckets) for velocity / acceleration.
_DEFAULT_SMOOTH = 3


# ── seasonal baseline ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class SeasonalBaseline:
    """Output of :func:`seasonal_baseline`.

    ``expected`` is the per-bucket multiplicative baseline (same length as the
    input). ``residual`` is the deseasonalised series ``observed - expected``.
    ``profile`` maps a ``(day_of_week, hour)`` slot to its multiplicative index
    (1.0 == average). ``seasonal`` is False when the series was too short and a
    flat-mean fallback was used.
    """

    expected: NDArray[np.float64]
    residual: NDArray[np.float64]
    profile: dict[tuple[int, int], float]
    mean: float
    seasonal: bool


def seasonal_baseline(
    counts: object,
    timestamps: list[datetime],
    *,
    period: int = 168,
) -> SeasonalBaseline:
    """Estimate a multiplicative day-of-week x hour-of-day expected profile.

    Parameters
    ----------
    counts:
        1-D non-negative count series.
    timestamps:
        One :class:`datetime` per count, used only to derive each bucket's
        ``(weekday, hour)`` slot. Must be the same length as ``counts``.
    period:
        Length of one full seasonal cycle in buckets. Defaults to 168 (one week
        of hourly buckets). Used to decide whether the series is long enough to
        support a seasonal estimate; the profile itself keys on (dow, hour).

    Returns
    -------
    SeasonalBaseline
        With the per-bucket ``expected`` baseline and ``residual`` series.

    Notes
    -----
    Multiplicative decomposition (``observed = mean * seasonal_index *
    residual``) is appropriate for count data whose variability scales with its
    level. The seasonal index for slot ``(d, h)`` is the mean of
    ``observed / global_mean`` over buckets in that slot; indices are normalised
    to average 1.0 so the baseline neither inflates nor deflates total volume.
    Slots with too few observations, or a series shorter than two full periods,
    fall back to the flat global mean (index 1.0) so short series degrade
    gracefully rather than over-fitting noise.
    """
    arr = np.asarray(counts, dtype=np.float64).ravel()
    n = arr.size
    if len(timestamps) != n:
        raise ValueError("counts and timestamps must have the same length")
    mean = float(arr.mean()) if n else 0.0

    # Short series: no reliable seasonality — fall back to a flat mean baseline.
    if n < _MIN_PERIODS_FOR_SEASONAL * period or mean <= 0.0:
        expected = np.full(n, mean, dtype=np.float64)
        return SeasonalBaseline(
            expected=expected,
            residual=arr - expected,
            profile={},
            mean=mean,
            seasonal=False,
        )

    slots = [(ts.weekday(), ts.hour) for ts in timestamps]
    # Accumulate per-slot sums and counts.
    slot_sum: dict[tuple[int, int], float] = {}
    slot_n: dict[tuple[int, int], int] = {}
    for slot, value in zip(slots, arr, strict=True):
        slot_sum[slot] = slot_sum.get(slot, 0.0) + float(value)
        slot_n[slot] = slot_n.get(slot, 0) + 1

    # Raw multiplicative index per slot (slot mean / global mean); under-sampled
    # slots default to 1.0 (== global mean).
    raw: dict[tuple[int, int], float] = {}
    for slot, count in slot_n.items():
        if count >= _MIN_SLOT_OBS:
            raw[slot] = (slot_sum[slot] / count) / mean
        else:
            raw[slot] = 1.0

    # Normalise indices so the weighted average index is exactly 1.0 — keeps the
    # baseline volume-neutral (classical seasonal-decomposition convention).
    total_weight = sum(slot_n[s] for s in raw)
    weighted = sum(raw[s] * slot_n[s] for s in raw) / total_weight if total_weight else 1.0
    norm = weighted if weighted > 0 else 1.0
    profile = {slot: idx / norm for slot, idx in raw.items()}

    expected = np.array([mean * profile.get(slot, 1.0) for slot in slots], dtype=np.float64)
    return SeasonalBaseline(
        expected=expected,
        residual=arr - expected,
        profile=profile,
        mean=mean,
        seasonal=True,
    )


# ── robust z-score ─────────────────────────────────────────────────────────────


def zscore_vs_baseline(counts: object, baseline: SeasonalBaseline) -> NDArray[np.float64]:
    """Robust (median/MAD) z-score of the deseasonalised residuals.

    Computes the modified z-score ``0.6745 * (r - median(r)) / MAD(r)`` of the
    residuals ``r = counts - baseline.expected`` (Iglewicz & Hoaglin 1993). The
    median/MAD pair is insensitive to the very spikes we are trying to detect, so
    a single large anomaly does not inflate the scale and mask itself. The scale
    is floored to avoid division by ~0 on a flat residual series.
    """
    arr = np.asarray(counts, dtype=np.float64).ravel()
    residual = arr - baseline.expected
    if residual.size == 0:
        return np.zeros(0, dtype=np.float64)
    median = float(np.median(residual))
    mad = float(np.median(np.abs(residual - median)))
    scale = max(mad / _MAD_TO_SIGMA, _MIN_SCALE)
    return (residual - median) / scale


# ── changepoints ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ChangepointResult:
    """Output of :func:`changepoints`.

    ``cusum_pos`` / ``cusum_neg`` are the per-bucket two-sided CUSUM statistics
    (always >= 0). ``indices`` are the buckets where an alarm fired (the CUSUM
    crossed ``h * sigma``). ``bocpd_prob`` is the per-bucket Bayesian probability
    that a changepoint occurred at that bucket (short run length), in [0, 1].
    """

    cusum_pos: NDArray[np.float64]
    cusum_neg: NDArray[np.float64]
    indices: list[int] = field(default_factory=list)
    bocpd_prob: NDArray[np.float64] = field(default_factory=lambda: np.zeros(0))


def changepoints(
    series: object,
    *,
    k: float = 0.5,
    h: float = 8.0,
    ref_alpha: float = 0.1,
    hazard: float = 1.0 / 50.0,
    bocpd: bool = True,
) -> ChangepointResult:
    """Two-sided CUSUM changepoint detection, with optional Bayesian variant.

    Parameters
    ----------
    series:
        1-D series to monitor (raw counts or, better, deseasonalised residuals).
    k:
        CUSUM slack / reference value in units of the series' robust sigma. Half
        the smallest shift you care about (Page 1954); 0.5 detects ~1-sigma
        shifts. Larger ``k`` ignores small drifts.
    h:
        Alarm threshold in robust-sigma units. The CUSUM fires when it exceeds
        ``h``. Larger ``h`` ⇒ fewer false alarms, slower detection. The default
        8.0 gives a high in-control average-run-length (rare false alarms on
        stationary noise) while still firing immediately on a real regime shift.
    ref_alpha:
        EWMA smoothing for the adaptive reference mean ``mu`` (``0 < a <= 1``).
        Smaller ⇒ longer memory / steadier reference. The reference forgets old
        values so a long run of same-sign noise cannot slowly accumulate into a
        false alarm, yet lags far enough behind a genuine step that the step
        still produces a sustained, detectable CUSUM excursion.
    hazard:
        Constant hazard rate for the Bayesian variant (prior prob. of a
        changepoint at any bucket ≈ ``hazard``; expected run length ``1/hazard``).
    bocpd:
        If True, also compute the Bayesian-online changepoint probability.

    Returns
    -------
    ChangepointResult

    Notes
    -----
    *CUSUM* (Page 1954) accumulates standardised deviations from an adaptive
    EWMA reference mean ``mu``::

        S_pos = max(0, S_pos + (x - mu)/sigma - k)
        S_neg = max(0, S_neg - (x - mu)/sigma - k)
        mu    = (1 - ref_alpha) * mu + ref_alpha * x   # while in control

    and alarms when either exceeds ``h``; on alarm both sums reset and ``mu`` is
    re-baselined to the post-change observation so successive shifts are each
    detected. ``sigma`` is estimated from the MAD of *successive differences*,
    which measures bucket-to-bucket noise and is unaffected by the level shift
    itself (a step perturbs only one difference), so the change cannot inflate
    the scale and hide itself.

    *BOCPD* (Adams & MacKay 2007) maintains a posterior over the current run
    length using a Gaussian observation model with a constant hazard; the mass on
    short run lengths (run length 0/1) is reported as the changepoint
    probability. Both methods are O(n) (BOCPD with a capped run-length window).
    """
    arr = np.asarray(series, dtype=np.float64).ravel()
    n = arr.size
    if n == 0:
        return ChangepointResult(
            cusum_pos=np.zeros(0),
            cusum_neg=np.zeros(0),
            indices=[],
            bocpd_prob=np.zeros(0),
        )

    # Scale estimate from the MAD of successive differences: this captures the
    # bucket-to-bucket *noise* and is immune to a level shift in the mean (a step
    # only perturbs one difference), unlike the raw std which the change itself
    # would inflate. The sqrt(2) corrects for differencing two i.i.d. samples.
    if n >= 2:
        diffs = np.diff(arr)
        mad_d = float(np.median(np.abs(diffs - np.median(diffs))))
        sigma = mad_d / (_MAD_TO_SIGMA * np.sqrt(2.0))
    else:
        sigma = 0.0
    sigma = max(sigma, _MIN_SCALE)

    s_pos = np.zeros(n, dtype=np.float64)
    s_neg = np.zeros(n, dtype=np.float64)
    indices: list[int] = []
    # Adaptive EWMA reference mean. Forgetting old values keeps a bounded memory
    # so a long run of same-sign noise cannot slowly accumulate into a false
    # alarm (the failure mode of an ever-growing cumulative mean), while the lag
    # is slow enough that a genuine step still drives a sustained CUSUM run. On
    # alarm we reset the statistics and re-baseline mu to the post-change value —
    # the changepoint-detection form of CUSUM (vs. the fixed-target control form).
    alpha = max(min(ref_alpha, 1.0), 1e-6)
    mu = float(arr[0])
    pos = 0.0
    neg = 0.0
    for t in range(n):
        z = (arr[t] - mu) / sigma
        pos = max(0.0, pos + z - k)
        neg = max(0.0, neg - z - k)
        s_pos[t] = pos
        s_neg[t] = neg
        if pos > h or neg > h:
            indices.append(t)
            pos = 0.0
            neg = 0.0
            mu = float(arr[t])
        else:
            mu = (1.0 - alpha) * mu + alpha * float(arr[t])

    bocpd_prob = (
        _bocpd_changepoint_prob(arr, hazard=hazard)
        if bocpd
        else np.zeros(n, dtype=np.float64)
    )
    return ChangepointResult(
        cusum_pos=s_pos,
        cusum_neg=s_neg,
        indices=indices,
        bocpd_prob=bocpd_prob,
    )


def _bocpd_changepoint_prob(
    arr: NDArray[np.float64], *, hazard: float, max_run: int = 256
) -> NDArray[np.float64]:
    """Per-bucket changepoint probability via Adams & MacKay (2007) BOCPD.

    Gaussian observation model with online-updated mean/variance per run length
    and a constant hazard. Returns ``P(run_length <= 1)`` at each bucket — the
    mass that a fresh segment just started — clipped to [0, 1]. The run-length
    distribution is truncated to ``max_run`` for O(n * max_run) cost.
    """
    n = arr.size
    if n == 0:
        return np.zeros(0, dtype=np.float64)

    # Global scale used as the observation noise (kept fixed for stability).
    var = max(float(np.var(arr)), _MIN_SCALE)
    obs_var = var

    # Run-length posterior R[r] = P(run length = r). Start certain at length 0.
    cap = min(max_run, n + 1)
    rl = np.zeros(cap, dtype=np.float64)
    rl[0] = 1.0
    # Sufficient statistics per run length: running sample mean.
    run_sum = np.zeros(cap, dtype=np.float64)
    run_cnt = np.zeros(cap, dtype=np.float64)

    out = np.zeros(n, dtype=np.float64)
    for t in range(n):
        x = float(arr[t])
        # Predictive mean per run length (prior mean = global mean for r=0).
        pred_mean = np.where(run_cnt > 0, run_sum / np.maximum(run_cnt, 1.0), float(arr.mean()))
        # Gaussian predictive likelihood of x under each run length.
        diff = x - pred_mean
        pred = np.exp(-0.5 * diff * diff / obs_var) / np.sqrt(2.0 * np.pi * obs_var)

        # Growth (run continues) and changepoint (run resets) messages.
        growth = rl * pred * (1.0 - hazard)
        cp_mass = float(np.sum(rl * pred * hazard))

        new_rl = np.zeros(cap, dtype=np.float64)
        new_rl[1:] = growth[:-1]  # length r → r+1
        new_rl[0] = cp_mass  # changepoint: back to length 0
        total = float(new_rl.sum())
        if total <= 0:
            new_rl[0] = 1.0
            total = 1.0
        new_rl /= total

        # Update sufficient statistics, shifting them alongside the run lengths.
        new_sum = np.zeros(cap, dtype=np.float64)
        new_cnt = np.zeros(cap, dtype=np.float64)
        new_sum[1:] = run_sum[:-1] + x
        new_cnt[1:] = run_cnt[:-1] + 1.0
        new_sum[0] = x
        new_cnt[0] = 1.0

        rl = new_rl
        run_sum = new_sum
        run_cnt = new_cnt
        # Probability the current run just (re)started.
        out[t] = float(rl[0] + (rl[1] if cap > 1 else 0.0))
    return np.clip(out, 0.0, 1.0)


# ── velocity / acceleration ─────────────────────────────────────────────────────


def _moving_average(arr: NDArray[np.float64], window: int) -> NDArray[np.float64]:
    """Centered moving average with edge-preserving (reflect) padding.

    Keeps the output the same length as the input and avoids the edge bias of a
    trailing average. ``window <= 1`` is a no-op.
    """
    if window <= 1 or arr.size == 0:
        return arr.astype(np.float64, copy=True)
    window = min(window, arr.size)
    pad = window // 2
    padded = np.pad(arr, pad, mode="edge")
    kernel = np.ones(window, dtype=np.float64) / window
    smoothed = np.convolve(padded, kernel, mode="same")
    return smoothed[pad : pad + arr.size]


def velocity(series: object, *, smooth: int = _DEFAULT_SMOOTH) -> NDArray[np.float64]:
    """Smoothed first difference (rate of change per bucket).

    The series is *differenced first*, then the difference series is smoothed
    with a small centered moving average to damp bucket-to-bucket noise. (We
    smooth the differences rather than the level to avoid the edge-padding of the
    moving average biasing the trailing point — the "now" value that emerging-
    trend scoring reads off.) The output keeps the input length with
    ``velocity[0] == 0`` (no prior bucket to difference against).
    """
    arr = np.asarray(series, dtype=np.float64).ravel()
    if arr.size == 0:
        return np.zeros(0, dtype=np.float64)
    if arr.size == 1:
        return np.zeros(1, dtype=np.float64)
    diff = np.diff(arr)  # length n-1
    smoothed = _moving_average(diff, smooth)
    return np.concatenate(([0.0], smoothed))


def acceleration(series: object, *, smooth: int = _DEFAULT_SMOOTH) -> NDArray[np.float64]:
    """Smoothed second difference (how fast the rate of change is changing).

    The first difference of :func:`velocity`; positive acceleration marks a
    series whose growth is itself accelerating (an emerging trend). Same
    length-preserving / edge-safe scheme as :func:`velocity`.
    """
    vel = velocity(series, smooth=smooth)
    if vel.size <= 1:
        return np.zeros(vel.size, dtype=np.float64)
    return np.diff(vel, prepend=vel[0])


__all__ = [
    "ChangepointResult",
    "SeasonalBaseline",
    "acceleration",
    "changepoints",
    "seasonal_baseline",
    "velocity",
    "zscore_vs_baseline",
]
