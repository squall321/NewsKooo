"""Backtest tests — IC (Spearman), hit-rate, CAR over an injected price series.

No market data: prices are a plain ``{(symbol, datetime): price}`` mapping built
synthetically so the signal/return relationship is known by construction.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

from newskoo.signals.backtest import (
    BacktestResult,
    SignalPoint,
    backtest,
)

_T0 = datetime(2026, 5, 1, 0, 0, 0, tzinfo=UTC)


def _make_case(*, correlated: bool) -> tuple[list[SignalPoint], dict]:
    """Build N signals + a 24h-forward price map.

    ``correlated``: higher score ⇒ higher forward return (monotone). Otherwise
    higher score ⇒ *lower* forward return (anti-correlated).
    """
    signals: list[SignalPoint] = []
    prices: dict[tuple[str, datetime], float] = {}
    n = 10
    for i in range(n):
        symbol = f"SYM{i}"
        score = -1.0 + 2.0 * i / (n - 1)  # spread across [-1, 1]
        as_of = _T0 + timedelta(days=i)
        t1 = as_of + timedelta(hours=24)
        # Forward return monotone in the score (or its negation).
        ret = score * 0.05 if correlated else -score * 0.05
        p0 = 100.0
        p1 = p0 * (1.0 + ret)
        signals.append(SignalPoint(symbol=symbol, as_of=as_of, score=score))
        prices[(symbol, as_of)] = p0
        prices[(symbol, t1)] = p1
    return signals, prices


def test_positive_relationship_ic_near_plus_one() -> None:
    signals, prices = _make_case(correlated=True)
    result = backtest(signals, prices, horizons=(24,))
    h = result.by_horizon(24)
    assert h is not None
    assert h.n == 10
    assert h.ic > 0.99  # strictly monotone ⇒ Spearman ≈ +1


def test_negative_relationship_ic_near_minus_one() -> None:
    signals, prices = _make_case(correlated=False)
    result = backtest(signals, prices, horizons=(24,))
    h = result.by_horizon(24)
    assert h is not None
    assert h.ic < -0.99


def test_hit_rate_high_when_signs_align() -> None:
    signals, prices = _make_case(correlated=True)
    h = backtest(signals, prices, horizons=(24,)).by_horizon(24)
    assert h is not None
    # Every non-flat signal has matching sign of forward return (the i with
    # score≈0 is excluded as flat); so hit rate is 1.0.
    assert h.hit_rate >= 0.99


def test_hit_rate_low_when_signs_oppose() -> None:
    signals, prices = _make_case(correlated=False)
    h = backtest(signals, prices, horizons=(24,)).by_horizon(24)
    assert h is not None
    assert h.hit_rate <= 0.01


def test_missing_prices_drop_observations() -> None:
    signals, prices = _make_case(correlated=True)
    # Drop one symbol's forward price entirely.
    del prices[("SYM3", _T0 + timedelta(days=3) + timedelta(hours=24))]
    h = backtest(signals, prices, horizons=(24,)).by_horizon(24)
    assert h is not None
    assert h.n == 9  # one observation dropped


def test_empty_signals_safe() -> None:
    result = backtest([], {}, horizons=(24, 72))
    assert isinstance(result, BacktestResult)
    assert result.n_signals == 0
    for h in result.horizons:
        assert h.n == 0
        assert h.ic == 0.0
        assert h.hit_rate == 0.0


def test_car_curve_length_matches_horizon_grid() -> None:
    signals, prices = _make_case(correlated=True)
    result = backtest(signals, prices, horizons=(24, 48, 72))
    assert [h.horizon_hours for h in result.horizons] == [24, 48, 72]
    # Each horizon's CAR curve cumulates out to its own grid index.
    for idx, h in enumerate(result.horizons):
        assert len(h.car_curve) == idx + 1
        assert math.isclose(h.car, h.car_curve[-1], rel_tol=1e-9)


def test_car_reduces_to_cumulative_mean_return_without_benchmark() -> None:
    # With prices only defined at as_of and as_of+24h (constant after), the
    # single-step CAR equals the mean forward return at 24h.
    signals, prices = _make_case(correlated=True)
    result = backtest(signals, prices, horizons=(24,))
    h = result.by_horizon(24)
    assert h is not None
    assert math.isclose(h.car, h.mean_forward_return, rel_tol=1e-9)


def test_market_adjustment_subtracts_benchmark() -> None:
    # If the benchmark moves exactly with the security, abnormal return ⇒ 0.
    signals, prices = _make_case(correlated=True)
    market = dict(prices)  # identical series ⇒ AR = 0 everywhere
    result = backtest(signals, prices, horizons=(24,), market_series=market)
    h = result.by_horizon(24)
    assert h is not None
    assert abs(h.car) < 1e-9


def test_price_series_callable_accessor() -> None:
    signals, prices = _make_case(correlated=True)

    def accessor(symbol: str, when: datetime) -> float | None:
        return prices.get((symbol, when))

    h = backtest(signals, accessor, horizons=(24,)).by_horizon(24)
    assert h is not None
    assert h.ic > 0.99
