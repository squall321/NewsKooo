"""Kleinberg-style burst detection over a non-negative count series.

Implements the finite-state infinite automaton from:

    J. Kleinberg, "Bursty and Hierarchical Structure in Streams",
    Proc. 8th ACM SIGKDD (2002). https://www.cs.cornell.edu/home/kleinberg/bhs.pdf

Intuition
---------
A stream of events (here: per-bucket mention *counts*) is modelled as being
emitted by an automaton with a ladder of states ``q_0, q_1, ...``. Higher
states emit events at faster rates and therefore *explain* dense regions
("bursts"), but the automaton pays a cost ``tau`` every time it ratchets *up*
to a higher (more bursty) state. The optimal state sequence is the one
minimising total cost = (state-transition cost) + (negative log-likelihood of
the observed counts under each state's rate). That minimisation is a Viterbi
dynamic program; the resulting per-bucket state index is the **burst level**,
and maximal runs of level ``>= 1`` are the **burst intervals**.

This is the discretised "counts per fixed-width bucket" formulation (Kleinberg
§4, the version used for document/word-count streams) rather than the
gap-based continuous model, because NewsKoo already aggregates mentions into
uniform :class:`~newskoo.models.timeseries.MentionTimeseries` buckets.

State rates
-----------
With ``n`` buckets totalling ``T`` events, the base rate is
``p_0 = T / n`` events/bucket. State ``i`` emits at ``p_i = p_0 * s**i`` where
``s > 1`` is the rate-scaling parameter. Each bucket's count is scored against a
Poisson likelihood with that state's expected rate. The upward-transition cost
is ``gamma * ln(n)`` per level climbed (Kleinberg's ``tau``); downward moves are
free. ``numpy`` only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

# Default rate scaling between adjacent automaton states (Kleinberg's ``s``).
_DEFAULT_S = 2.0
# Default transition-cost weight (Kleinberg's ``gamma``).
_DEFAULT_GAMMA = 1.0
# Hard cap on automaton states so the DP stays O(n * k) for pathological inputs.
_MAX_STATES = 16
# Numerical floor for any Poisson rate so ``ln(rate)`` and ``count/rate`` are
# finite even when the whole series is zero.
_MIN_RATE = 1e-9


@dataclass(frozen=True)
class BurstInterval:
    """A maximal run of buckets at burst level ``>= 1``.

    ``start``/``end`` are inclusive bucket indices into the input series.
    ``level`` is the peak (max) burst level reached inside the interval.
    ``weight`` is the accumulated burst weight (Kleinberg §6): the cost saved by
    using the bursty states over the base state across the interval — useful for
    ranking one burst against another.
    """

    start: int
    end: int
    level: int
    weight: float


@dataclass(frozen=True)
class BurstResult:
    """Result of :func:`detect_bursts`.

    ``levels`` is the per-bucket optimal burst level (0 = baseline). ``intervals``
    are the maximal bursty runs. ``base_rate`` is ``p_0`` (events/bucket).
    ``n_states`` is the size of the state ladder actually used.
    """

    levels: NDArray[np.int_]
    intervals: list[BurstInterval] = field(default_factory=list)
    base_rate: float = 0.0
    n_states: int = 1


def _coerce_counts(counts: object) -> NDArray[np.float64]:
    """Validate and return counts as a 1-D non-negative float array."""
    arr = np.asarray(counts, dtype=np.float64).ravel()
    if arr.size and (arr < 0).any():
        raise ValueError("burst detection requires a non-negative count series")
    if not np.isfinite(arr).all():
        raise ValueError("burst detection requires a finite count series")
    return arr


def _n_states(total: float, base_rate: float, s: float) -> int:
    """Pick how many states the ladder needs to reach the densest bucket.

    We only need enough states that the top state's rate ``p_0 * s**(k-1)``
    comfortably exceeds the largest single-bucket count; more states would never
    be selected by the DP and only cost time.
    """
    if total <= 0 or base_rate <= 0:
        return 1
    peak = max(total, base_rate)
    # Smallest k with base_rate * s**(k-1) >= peak  ⇒  k >= 1 + log_s(peak/base).
    k = 1 + math.ceil(math.log(peak / base_rate, s)) if peak > base_rate else 1
    return int(min(max(k, 2), _MAX_STATES))


def _poisson_cost(count: float, rate: float) -> float:
    """Negative log-likelihood of ``count`` under a Poisson with mean ``rate``.

    Drops the ``ln(count!)`` term: it is identical across states for a given
    bucket and so cancels out of the arg-min. Returns ``rate - count*ln(rate)``.
    """
    rate = max(rate, _MIN_RATE)
    return rate - count * math.log(rate)


def detect_bursts(
    counts: object,
    *,
    s: float = _DEFAULT_S,
    gamma: float = _DEFAULT_GAMMA,
) -> BurstResult:
    """Detect bursts in a non-negative ``counts`` series (Kleinberg 2002).

    Parameters
    ----------
    counts:
        1-D sequence of non-negative per-bucket event counts.
    s:
        Rate scaling between adjacent states (``> 1``). State ``i`` emits at
        ``p_0 * s**i``. Larger ``s`` ⇒ fewer, sharper burst levels. Default 2.0.
    gamma:
        Weight on the upward state-transition cost (``gamma * ln(n)`` per level).
        Larger ``gamma`` ⇒ harder to enter a burst, so only stronger anomalies
        register. Default 1.0.

    Returns
    -------
    BurstResult
        Per-bucket burst ``levels`` and the maximal ``intervals`` of level >= 1.

    Notes
    -----
    The optimal state path minimises::

        sum_t poisson_cost(count_t, p_{q_t})  +  sum_t transition_cost(q_{t-1}, q_t)

    via a Viterbi DP over ``n`` buckets and ``k`` states (O(n*k)). Upward moves
    of ``d`` levels cost ``d * gamma * ln(n)``; staying or descending is free
    (Kleinberg §4). Costs are accumulated in natural log so they compose
    additively and avoid underflow.
    """
    if s <= 1.0:
        raise ValueError("rate-scaling 's' must be > 1")
    if gamma < 0.0:
        raise ValueError("transition weight 'gamma' must be >= 0")

    arr = _coerce_counts(counts)
    n = arr.size
    if n == 0:
        return BurstResult(levels=np.zeros(0, dtype=np.int_), base_rate=0.0, n_states=1)

    total = float(arr.sum())
    base_rate = total / n
    if base_rate <= 0:
        # Empty/all-zero stream: nothing can burst.
        return BurstResult(levels=np.zeros(n, dtype=np.int_), base_rate=0.0, n_states=1)

    k = _n_states(total, base_rate, s)
    rates = base_rate * (s ** np.arange(k, dtype=np.float64))

    # Upward-transition cost matrix: tau[i, j] = cost of moving from state i→j.
    tau = gamma * math.log(max(n, 2))
    # Per-bucket Poisson cost for every state, precomputed.
    emit = np.empty((n, k), dtype=np.float64)
    for j in range(k):
        rate_j = float(rates[j])
        for t in range(n):
            emit[t, j] = _poisson_cost(float(arr[t]), rate_j)

    # Viterbi DP. cost[j] = min total cost of a path ending in state j at bucket t.
    cost = emit[0].copy()
    # Entering any state above base at the very first bucket still pays the climb
    # from the implicit baseline q_0 (Kleinberg starts the automaton in q_0).
    for j in range(1, k):
        cost[j] += j * tau
    back = np.zeros((n, k), dtype=np.int_)

    for t in range(1, n):
        prev = cost
        new = np.empty(k, dtype=np.float64)
        for j in range(k):
            # Transition cost into j from each previous state i (up = j-i climbs).
            trans = np.where(
                np.arange(k) < j,
                (j - np.arange(k)) * tau,  # climbing up costs
                0.0,  # staying or descending is free
            )
            candidate = prev + trans
            i_best = int(np.argmin(candidate))
            back[t, j] = i_best
            new[j] = candidate[i_best] + emit[t, j]
        cost = new

    # Backtrack the optimal state sequence.
    levels = np.zeros(n, dtype=np.int_)
    j = int(np.argmin(cost))
    levels[n - 1] = j
    for t in range(n - 1, 0, -1):
        j = int(back[t, j])
        levels[t - 1] = j

    intervals = _extract_intervals(levels, emit)
    return BurstResult(
        levels=levels,
        intervals=intervals,
        base_rate=base_rate,
        n_states=k,
    )


def _extract_intervals(
    levels: NDArray[np.int_], emit: NDArray[np.float64]
) -> list[BurstInterval]:
    """Group maximal runs of level >= 1 into :class:`BurstInterval`s.

    A burst's ``weight`` is the total likelihood cost the baseline state would
    have paid minus the cost the chosen states paid across the run (Kleinberg's
    burst "weight", §6) — strictly positive for a genuine burst.
    """
    intervals: list[BurstInterval] = []
    n = levels.size
    t = 0
    while t < n:
        if levels[t] < 1:
            t += 1
            continue
        start = t
        peak = int(levels[t])
        weight = 0.0
        while t < n and levels[t] >= 1:
            lvl = int(levels[t])
            peak = max(peak, lvl)
            # Cost saved vs. staying in the base state (state 0) at this bucket.
            weight += float(emit[t, 0] - emit[t, lvl])
            t += 1
        intervals.append(
            BurstInterval(start=start, end=t - 1, level=peak, weight=round(weight, 6))
        )
    return intervals


__all__ = ["BurstInterval", "BurstResult", "detect_bursts"]
