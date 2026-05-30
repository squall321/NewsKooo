"""Signal backtesting — does the signal predict forward returns?

Deliberately **decoupled from any market-data source**: the caller injects a
``price_series``, a mapping or callable ``(symbol, datetime) -> price | None``.
This keeps the module pure (no network, no vendor SDK, deterministic tests) and
lets the same code run against a CSV in a test, a vendor API in research, or a
live store in production — only the injected accessor changes (see "Feeding real
prices" below).

Inputs
------
* ``signals`` — an iterable of :class:`SignalPoint` (symbol, as_of, score). A
  thin value object so callers can feed ORM :class:`~newskoo.models.finance.Signal`
  rows *or* synthetic points without a DB.
* ``price_series`` — ``(symbol, when) -> float | None``. ``None`` means "no price
  at/near that time" and the observation is dropped.
* ``horizons`` — forward windows in hours, e.g. ``(24, 72, 168)``. Metrics are
  computed per horizon.

Per-horizon metrics (per :class:`HorizonResult`)
------------------------------------------------
For each signal we take the price at ``as_of`` (``p0``) and at ``as_of + h``
(``p1``); the **forward return** is ``r = p1 / p0 - 1``.

* **Information Coefficient (IC)** — Spearman rank correlation between the signal
  scores and the forward returns. Spearman (rank, not Pearson/level) is the
  standard signal-quality metric: it is monotone-invariant and robust to the
  heavy tails of returns. IC ∈ [-1, 1]; +1 = perfectly ordered, -1 = perfectly
  inverted, 0 = no rank relationship. Computed as Pearson correlation of the
  *ranks* (average ranks for ties).
* **Hit rate** — fraction of observations where ``sign(score) == sign(r)``,
  counting only non-flat signals/returns (``|score| > eps`` and ``r != 0``). A
  directional-accuracy measure complementary to IC's ordering view.
* **CAR (event-study cumulative abnormal return)** — average **abnormal** return
  across the event window, cumulated. The abnormal return strips a benchmark
  (market) return so we measure the signal's *excess* explanatory power, not beta
  to the tape::

        AR_i(τ)   = r_i(τ)  - r_market(τ)              (abnormal return, step τ)
        AAR(τ)    = mean_i AR_i(τ)                     (average across events)
        CAR(τ)    = Σ_{k≤τ} AAR(k)                     (cumulated over the window)

  We sample the event window at the requested horizon's sub-steps (each prior
  horizon is a step) so ``car`` is the cumulative average abnormal return out to
  ``h``. With no benchmark supplied the market return is 0 and CAR reduces to the
  cumulative average *raw* return (still a valid event-study curve, just not
  market-adjusted). ``car`` on a :class:`HorizonResult` is the terminal value;
  the full curve is in ``car_curve``.

All math is pure numpy; no SciPy dependency (Spearman is implemented here).

Feeding real prices later
--------------------------
``price_series`` is the only seam. Examples::

    # dict of (symbol, datetime) -> close
    prices = {("AAPL", dt0): 190.1, ("AAPL", dt1): 192.4, ...}
    backtest(signals, prices, horizons=(24, 72))

    # callable wrapping a vendor client / DB (still no import here)
    def prices(symbol: str, when: datetime) -> float | None:
        return vendor.close_on_or_before(symbol, when)
    backtest(signals, prices, horizons=(24,))

A benchmark accessor (same shape) can be passed as ``market_series`` to make the
abnormal-return adjustment real (e.g. SPY or the security's index).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import numpy as np

# A price accessor: explicit mapping keyed by (symbol, datetime), or a callable.
PriceSeries = Mapping[tuple[str, datetime], float] | Callable[[str, datetime], "float | None"]

_EPS: float = 1e-12


@dataclass(slots=True)
class SignalPoint:
    """A backtestable signal observation (DB-free value object)."""

    symbol: str
    as_of: datetime
    score: float


@dataclass(slots=True)
class HorizonResult:
    """Metrics for one forward horizon (hours)."""

    horizon_hours: int
    n: int  # usable observations (both p0 and p1 priced)
    ic: float  # Spearman rank corr(score, forward return)
    hit_rate: float  # fraction with sign(score)==sign(return)
    mean_forward_return: float  # average forward return
    car: float  # terminal cumulative (abnormal) return of the event study
    car_curve: list[float] = field(default_factory=list)  # CAR at each sub-step


@dataclass(slots=True)
class BacktestResult:
    """Full backtest output across all requested horizons."""

    horizons: list[HorizonResult]
    n_signals: int  # total input signals considered

    def by_horizon(self, hours: int) -> HorizonResult | None:
        """Return the :class:`HorizonResult` for ``hours`` (or ``None``)."""
        for h in self.horizons:
            if h.horizon_hours == hours:
                return h
        return None


def _price_at(series: PriceSeries, symbol: str, when: datetime) -> float | None:
    """Look up a price via mapping or callable; ``None`` if unavailable."""
    if callable(series):
        return series(symbol, when)
    return series.get((symbol, when))


def _spearman(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rank correlation of two 1-D arrays (ties → average ranks).

    Returns 0.0 when fewer than two points or when either side has zero rank
    variance (all-equal), since correlation is undefined there.
    """
    if x.size < 2:
        return 0.0
    rx = _rankdata(x)
    ry = _rankdata(y)
    sx = rx.std()
    sy = ry.std()
    if sx < _EPS or sy < _EPS:
        return 0.0
    return float(np.clip(np.corrcoef(rx, ry)[0, 1], -1.0, 1.0))


def _rankdata(a: np.ndarray) -> np.ndarray:
    """Average ranks of ``a`` (1-based), ties share the mean of their ranks.

    Mirrors ``scipy.stats.rankdata`` (method='average') without the dependency.
    """
    order = a.argsort(kind="mergesort")
    ranks = np.empty(a.size, dtype=np.float64)
    ranks[order] = np.arange(1, a.size + 1, dtype=np.float64)
    # Average ranks within tie groups (equal values).
    sorted_a = a[order]
    i = 0
    n = a.size
    while i < n:
        j = i + 1
        while j < n and sorted_a[j] == sorted_a[i]:
            j += 1
        if j - i > 1:
            avg = (np.arange(i + 1, j + 1, dtype=np.float64)).mean()
            ranks[order[i:j]] = avg
        i = j
    return ranks


def _forward_return(
    series: PriceSeries, symbol: str, t0: datetime, t1: datetime
) -> float | None:
    """``p(t1)/p(t0) - 1`` or ``None`` if either price is missing/degenerate."""
    p0 = _price_at(series, symbol, t0)
    p1 = _price_at(series, symbol, t1)
    if p0 is None or p1 is None or abs(p0) < _EPS:
        return None
    return p1 / p0 - 1.0


def backtest(
    signals: Iterable[SignalPoint],
    price_series: PriceSeries,
    *,
    horizons: Iterable[int],
    market_series: PriceSeries | None = None,
) -> BacktestResult:
    """Backtest ``signals`` against an injected ``price_series`` per horizon.

    See the module docstring for the metric definitions (IC = Spearman rank
    corr, hit-rate = directional accuracy, CAR = cumulative average abnormal
    return event-study). ``market_series`` (optional, same shape) supplies the
    benchmark for the abnormal-return adjustment; absent it, CAR is the
    cumulative average raw return.
    """
    sigs = list(signals)
    horizon_list = sorted({int(h) for h in horizons})
    results: list[HorizonResult] = []

    # Event-study sub-steps: the sorted horizons themselves are the cumulation
    # grid (CAR at step k = average abnormal return out to horizons[k]).
    for h in horizon_list:
        scores: list[float] = []
        rets: list[float] = []
        for s in sigs:
            t1 = s.as_of + timedelta(hours=h)
            r = _forward_return(price_series, s.symbol, s.as_of, t1)
            if r is None:
                continue
            scores.append(s.score)
            rets.append(r)

        n = len(rets)
        if n == 0:
            results.append(
                HorizonResult(h, 0, 0.0, 0.0, 0.0, 0.0, [0.0 for _ in horizon_list])
            )
            continue

        score_arr = np.asarray(scores, dtype=np.float64)
        ret_arr = np.asarray(rets, dtype=np.float64)

        ic = _spearman(score_arr, ret_arr)

        # Hit rate over non-flat observations.
        nonflat = (np.abs(score_arr) > 1e-9) & (np.abs(ret_arr) > _EPS)
        if nonflat.any():
            hits = np.sign(score_arr[nonflat]) == np.sign(ret_arr[nonflat])
            hit_rate = float(hits.mean())
        else:
            hit_rate = 0.0

        mean_fwd = float(ret_arr.mean())

        results.append(
            HorizonResult(
                horizon_hours=h,
                n=n,
                ic=ic,
                hit_rate=hit_rate,
                mean_forward_return=mean_fwd,
                car=0.0,  # filled below once the curve is built
                car_curve=[],
            )
        )

    # ── Event-study CAR curve over the horizon grid ──────────────────────────
    # AAR(step k) = mean over signals of the abnormal return between the
    # previous grid point and horizons[k]; CAR cumulates these. Computed once
    # over the shared grid and attached to the *terminal* horizon's result while
    # each intermediate result gets its own truncated curve.
    aar: list[float] = []
    prev = 0  # hours of the previous grid point (0 = signal time)
    for h in horizon_list:
        step_abnormals: list[float] = []
        for s in sigs:
            t_prev = s.as_of + timedelta(hours=prev)
            t_cur = s.as_of + timedelta(hours=h)
            r = _forward_return(price_series, s.symbol, t_prev, t_cur)
            if r is None:
                continue
            if market_series is not None:
                m = _forward_return(market_series, s.symbol, t_prev, t_cur)
                if m is not None:
                    r = r - m
            step_abnormals.append(r)
        aar.append(float(np.mean(step_abnormals)) if step_abnormals else 0.0)
        prev = h

    car_curve = np.cumsum(np.asarray(aar, dtype=np.float64)).tolist()
    for idx, res in enumerate(results):
        # Each horizon's CAR is the cumulative abnormal return out to that point.
        res.car_curve = car_curve[: idx + 1]
        res.car = car_curve[idx]

    return BacktestResult(horizons=results, n_signals=len(sigs))
