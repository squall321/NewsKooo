"""Per-article and per-event news *impact* — the atomic unit of a signal.

A signal for a security is an aggregate of the impacts of the individual news
items mentioning it. This module is the pure, side-effect-free core: given the
analysis features of one article (or one clustered event) it returns a signed
:class:`Impact` in [-1, 1]. :mod:`newskoo.signals.generate` does the DB I/O and
the aggregation.

Math
----
**Recency decay.** News goes stale: a headline from three days ago should move a
signal far less than one from an hour ago. We weight each item by an exponential
decay with a configurable half-life ``H`` (``settings.signal_half_life_hours``,
default 24h)::

    decay(age, H) = 2 ** (-age / H)          (age in hours, age >= 0)

so ``decay(0) = 1``, ``decay(H) = 1/2``, ``decay(2H) = 1/4`` — a clean,
unit-free half-life interpretation. (Equivalently ``exp(-λ·age)`` with
``λ = ln2 / H``.) Negative ages (clock skew / future timestamps) are clamped to 0
so a slightly-future article is treated as "now", never amplified.

**Article impact.** Four features, each in a documented range, combine into a
signed impact:

* ``sentiment``  ∈ [-1, 1] — directional polarity (the *sign* of the impact).
* ``magnitude``  ∈ [0, 1]  — how strongly the article is *about* the security
  (salience · confidence upstream); scales the raw size.
* ``novelty``    ∈ [0, 1]  — new information vs. a rehash of known facts; a
  near-duplicate (novelty≈0) should barely move the signal. Folded in as a
  multiplicative *gate* with a floor so a non-novel but on-topic article still
  contributes a little.
* ``source_credibility`` ∈ [0, 1] — trust in the outlet (integration point #3);
  also a multiplicative gate with a floor (unknown source ⇒ neutral-ish weight,
  not zero).

The unsigned *strength* is the product of the magnitude and the two gated
quality factors, then decayed by recency::

    novelty_gate = NOVELTY_FLOOR + (1 - NOVELTY_FLOOR) * novelty
    cred_gate    = CRED_FLOOR    + (1 - CRED_FLOOR)    * source_credibility
    strength     = clip(magnitude, 0, 1) * novelty_gate * cred_gate
    weight       = decay(age_hours, half_life)
    score        = clip(sentiment, -1, 1) * strength * weight

The result is in [-1, 1]: the sign follows sentiment polarity, the magnitude is
bounded by ``|sentiment| ≤ 1`` times a product of factors each in [0, 1] times a
decay weight in (0, 1]. ``components`` records every factor for audit / the
``Signal.components`` JSONB. ``confidence`` of a single item is the
recency-and-quality weight itself (how much we should trust this one data point),
distinct from the directional ``score``.

**Event impact.** An event is a cluster of articles about one real-world story.
``event_impact`` aggregates member impacts the same way the signal generator
aggregates per-security: a weight-weighted mean of member scores (weights =
member strengths · decay), so a 50-article story dominates a 2-article one and
recent members dominate stale ones. The event's own ``magnitude``/``confidence``
reflect the summed weight (saturating), and ``direction`` follows the sign.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# ── Gate floors ───────────────────────────────────────────────────────────────
# A non-novel but on-topic article, or an article from an unknown-credibility
# source, should still contribute *something* rather than being zeroed out. These
# floors set the minimum multiplier each gate can apply (so the gate ranges
# [floor, 1] as its input ranges [0, 1]).
NOVELTY_FLOOR: float = 0.25
CRED_FLOOR: float = 0.40

# Saturation constant for turning a summed weight into a [0, 1) confidence:
# conf = 1 - exp(-total_weight / TAU). With TAU = 2 a single full-weight article
# yields ~0.39 confidence, ~3 yield ~0.78, ~6 yield ~0.95 — diminishing returns
# in sample size, as desired for a news-volume confidence.
_CONF_TAU: float = 2.0

# Sentiment magnitudes below this are treated as no directional signal, so a
# near-zero-polarity article maps to a "neutral" direction rather than a
# coin-flip bullish/bearish.
_NEUTRAL_EPS: float = 1e-9


def _clip(x: float, lo: float, hi: float) -> float:
    """Clamp ``x`` to ``[lo, hi]``."""
    return lo if x < lo else hi if x > hi else x


def _direction(score: float) -> str:
    """Categorical projection of a signed score → bullish | bearish | neutral."""
    if score > _NEUTRAL_EPS:
        return "bullish"
    if score < -_NEUTRAL_EPS:
        return "bearish"
    return "neutral"


@dataclass(slots=True)
class Impact:
    """A signed news impact and its audit trail.

    * ``score``      — signed conviction in [-1, 1].
    * ``direction``  — ``bullish`` / ``bearish`` / ``neutral`` (sign of score).
    * ``magnitude``  — unsigned strength in [0, 1] (``abs(score)`` for an
      article; the saturated aggregate strength for an event).
    * ``confidence`` — trust in this data point in [0, 1] (the recency/quality
      weight for an article; the saturated summed weight for an event).
    * ``components`` — the factors that produced the score (for ``Signal.components``).
    """

    score: float
    direction: str
    magnitude: float
    confidence: float
    components: dict[str, float] = field(default_factory=dict)


def decay(age_hours: float, half_life: float) -> float:
    """Exponential recency weight with a half-life of ``half_life`` hours.

    ``decay(0, H) == 1``; ``decay(H, H) == 0.5``; halves every ``H`` hours.
    Negative ages (future timestamps from clock skew) are clamped to 0, so a
    near-future item is treated as "now" and never amplified above 1. A
    non-positive ``half_life`` is degenerate (no decay) and returns 1.0.
    """
    if half_life <= 0:
        return 1.0
    age = age_hours if age_hours > 0.0 else 0.0
    return math.pow(2.0, -age / half_life)


def article_impact(
    *,
    sentiment: float,
    magnitude: float,
    novelty: float,
    source_credibility: float,
    age_hours: float,
    half_life: float = 24.0,
) -> Impact:
    """Signed impact in [-1, 1] of a single article (see module docstring math).

    The sign follows ``sentiment``; the size is the article's topical
    ``magnitude`` gated by ``novelty`` and ``source_credibility`` (each with a
    floor) and decayed by recency (``age_hours`` against ``half_life``).
    """
    s = _clip(sentiment, -1.0, 1.0)
    mag = _clip(magnitude, 0.0, 1.0)
    nov = _clip(novelty, 0.0, 1.0)
    cred = _clip(source_credibility, 0.0, 1.0)

    novelty_gate = NOVELTY_FLOOR + (1.0 - NOVELTY_FLOOR) * nov
    cred_gate = CRED_FLOOR + (1.0 - CRED_FLOOR) * cred
    weight = decay(age_hours, half_life)

    strength = mag * novelty_gate * cred_gate
    score = _clip(s * strength * weight, -1.0, 1.0)

    components = {
        "sentiment": s,
        "magnitude": mag,
        "novelty": nov,
        "novelty_gate": novelty_gate,
        "source_credibility": cred,
        "cred_gate": cred_gate,
        "age_hours": float(age_hours),
        "decay_weight": weight,
        "strength": strength,
    }
    return Impact(
        score=score,
        direction=_direction(score),
        magnitude=abs(score),
        confidence=strength * weight,
        components=components,
    )


def event_impact(
    members: list[Impact],
    *,
    half_life: float = 24.0,
) -> Impact:
    """Aggregate member article impacts into one event-level :class:`Impact`.

    Weight-weighted mean of member ``score``s, weights = member ``confidence``
    (which already folds in each member's strength · recency decay), so a
    high-volume, recent, credible story dominates. The aggregate ``confidence``
    saturates with the *summed* member weight (more corroborating articles ⇒
    more confidence, with diminishing returns), and ``direction`` follows the
    aggregate sign.

    An empty cluster (or one whose members all carry zero weight) yields a
    neutral zero-impact result.
    """
    if not members:
        return Impact(0.0, "neutral", 0.0, 0.0, {"n_members": 0.0, "total_weight": 0.0})

    total_weight = sum(m.confidence for m in members)
    if total_weight <= 0.0:
        # All members fully decayed / zero strength: no usable signal.
        return Impact(
            0.0,
            "neutral",
            0.0,
            0.0,
            {"n_members": float(len(members)), "total_weight": 0.0},
        )

    weighted = sum(m.score * m.confidence for m in members) / total_weight
    score = _clip(weighted, -1.0, 1.0)
    confidence = 1.0 - math.exp(-total_weight / _CONF_TAU)
    # Agreement: |mean| / mean(|.|) in [0, 1] — 1 when members all agree in sign,
    # toward 0 when they cancel. Magnitude is the unsigned aggregate, scaled so a
    # conflicted cluster reports a smaller magnitude than its raw |mean|.
    abs_mean = (
        sum(abs(m.score) * m.confidence for m in members) / total_weight
    )
    agreement = abs(weighted) / abs_mean if abs_mean > 0.0 else 0.0
    components = {
        "n_members": float(len(members)),
        "total_weight": total_weight,
        "weighted_mean": weighted,
        "agreement": agreement,
    }
    return Impact(
        score=score,
        direction=_direction(score),
        magnitude=abs(score),
        confidence=confidence,
        components=components,
    )
