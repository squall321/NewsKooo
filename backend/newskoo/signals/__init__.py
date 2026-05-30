"""Financial / equities signal layer — turn news into tradeable signals.

NewsKoo's ultimate goal. Layers:

* :mod:`securities` — the tradeable-instrument catalog (:data:`SECURITIES` seed +
  :func:`seed_securities`) and the news→market bridge
  (:func:`link_entities_to_securities`: symbol/name/alias + RapidFuzz matching of
  :class:`~newskoo.models.taxonomy.Entity` rows to
  :class:`~newskoo.models.finance.Security` rows).
* :mod:`impact` — pure scoring of one news item: :func:`decay` (exponential
  recency weight), :func:`article_impact` / :func:`event_impact` →
  :class:`Impact` (signed score in [-1, 1] + components).
* :mod:`generate` — :func:`generate_signals`: gather recent linked news per
  security, aggregate decayed impacts, persist :class:`~newskoo.models.finance.Signal`
  rows.
* :mod:`backtest` — :func:`backtest`: market-data-free event study over an
  *injected* price series → per-horizon IC (Spearman), hit-rate and CAR
  (:class:`BacktestResult`).
"""

from __future__ import annotations

from newskoo.signals.backtest import (
    BacktestResult,
    HorizonResult,
    SignalPoint,
    backtest,
)
from newskoo.signals.generate import generate_signals
from newskoo.signals.impact import (
    Impact,
    article_impact,
    decay,
    event_impact,
)
from newskoo.signals.securities import (
    FUZZY_THRESHOLD,
    SECURITIES,
    link_entities_to_securities,
    seed_securities,
)

__all__ = [
    "FUZZY_THRESHOLD",
    "SECURITIES",
    "BacktestResult",
    "HorizonResult",
    "Impact",
    "SignalPoint",
    "article_impact",
    "backtest",
    "decay",
    "event_impact",
    "generate_signals",
    "link_entities_to_securities",
    "seed_securities",
]
