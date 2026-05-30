"""Impact math tests — sign, decay monotonicity, gates, event aggregation."""

from __future__ import annotations

import itertools
import math

from newskoo.signals.impact import (
    CRED_FLOOR,
    NOVELTY_FLOOR,
    Impact,
    article_impact,
    decay,
    event_impact,
)


# ── decay ─────────────────────────────────────────────────────────────────────
def test_decay_half_life_semantics() -> None:
    assert decay(0.0, 24.0) == 1.0
    assert math.isclose(decay(24.0, 24.0), 0.5, rel_tol=1e-9)
    assert math.isclose(decay(48.0, 24.0), 0.25, rel_tol=1e-9)


def test_decay_clamps_negative_age() -> None:
    # Future timestamps (clock skew) are treated as "now", never amplified.
    assert decay(-10.0, 24.0) == 1.0


def test_decay_monotone_decreasing() -> None:
    weights = [decay(a, 24.0) for a in (0, 6, 12, 24, 48, 96)]
    assert all(a > b for a, b in itertools.pairwise(weights))


def test_decay_degenerate_half_life() -> None:
    assert decay(100.0, 0.0) == 1.0


# ── article_impact sign ───────────────────────────────────────────────────────
def test_positive_sentiment_positive_score() -> None:
    imp = article_impact(
        sentiment=0.8, magnitude=1.0, novelty=1.0, source_credibility=1.0, age_hours=0.0
    )
    assert imp.score > 0
    assert imp.direction == "bullish"


def test_negative_sentiment_negative_score() -> None:
    imp = article_impact(
        sentiment=-0.8, magnitude=1.0, novelty=1.0, source_credibility=1.0, age_hours=0.0
    )
    assert imp.score < 0
    assert imp.direction == "bearish"


def test_zero_sentiment_neutral() -> None:
    imp = article_impact(
        sentiment=0.0, magnitude=1.0, novelty=1.0, source_credibility=1.0, age_hours=0.0
    )
    assert imp.score == 0.0
    assert imp.direction == "neutral"


# ── decay reduces magnitude ───────────────────────────────────────────────────
def test_older_article_smaller_magnitude() -> None:
    fresh = article_impact(
        sentiment=0.7, magnitude=1.0, novelty=1.0, source_credibility=1.0, age_hours=0.0
    )
    old = article_impact(
        sentiment=0.7, magnitude=1.0, novelty=1.0, source_credibility=1.0, age_hours=72.0
    )
    assert abs(old.score) < abs(fresh.score)
    assert old.confidence < fresh.confidence
    # Same sign though.
    assert math.copysign(1, old.score) == math.copysign(1, fresh.score)


def test_score_within_unit_interval() -> None:
    imp = article_impact(
        sentiment=1.0, magnitude=1.0, novelty=1.0, source_credibility=1.0, age_hours=0.0
    )
    assert -1.0 <= imp.score <= 1.0
    assert imp.score == 1.0  # all factors maxed, no decay


# ── components present ────────────────────────────────────────────────────────
def test_components_recorded() -> None:
    imp = article_impact(
        sentiment=0.5, magnitude=0.6, novelty=0.4, source_credibility=0.7, age_hours=12.0
    )
    for key in (
        "sentiment",
        "magnitude",
        "novelty",
        "novelty_gate",
        "source_credibility",
        "cred_gate",
        "decay_weight",
        "strength",
    ):
        assert key in imp.components


# ── gates: floors and monotonicity ────────────────────────────────────────────
def test_novelty_gate_floor() -> None:
    # novelty=0 still contributes (floored), but less than novelty=1.
    low = article_impact(
        sentiment=1.0, magnitude=1.0, novelty=0.0, source_credibility=1.0, age_hours=0.0
    )
    high = article_impact(
        sentiment=1.0, magnitude=1.0, novelty=1.0, source_credibility=1.0, age_hours=0.0
    )
    assert low.score > 0
    assert math.isclose(low.components["novelty_gate"], NOVELTY_FLOOR, rel_tol=1e-9)
    assert low.score < high.score


def test_credibility_gate_floor() -> None:
    low = article_impact(
        sentiment=1.0, magnitude=1.0, novelty=1.0, source_credibility=0.0, age_hours=0.0
    )
    assert math.isclose(low.components["cred_gate"], CRED_FLOOR, rel_tol=1e-9)
    assert 0 < low.score < 1.0


def test_inputs_clamped() -> None:
    # Out-of-range inputs are clamped, not propagated.
    imp = article_impact(
        sentiment=5.0, magnitude=9.0, novelty=2.0, source_credibility=-3.0, age_hours=0.0
    )
    assert imp.components["sentiment"] == 1.0
    assert imp.components["magnitude"] == 1.0
    assert imp.components["novelty"] == 1.0
    assert imp.components["source_credibility"] == 0.0


# ── event_impact aggregation ──────────────────────────────────────────────────
def test_event_impact_empty_is_neutral() -> None:
    ev = event_impact([])
    assert ev.score == 0.0
    assert ev.direction == "neutral"
    assert ev.confidence == 0.0


def test_event_impact_weighted_mean_and_agreement() -> None:
    members = [
        article_impact(sentiment=0.8, magnitude=1.0, novelty=1.0, source_credibility=1.0, age_hours=0.0),
        article_impact(sentiment=0.6, magnitude=1.0, novelty=1.0, source_credibility=1.0, age_hours=0.0),
    ]
    ev = event_impact(members)
    assert ev.score > 0
    assert ev.direction == "bullish"
    # Unanimous direction → high agreement.
    assert ev.components["agreement"] > 0.99
    assert 0.0 < ev.confidence < 1.0


def test_event_impact_conflicting_members_cancel() -> None:
    members = [
        article_impact(sentiment=0.9, magnitude=1.0, novelty=1.0, source_credibility=1.0, age_hours=0.0),
        article_impact(sentiment=-0.9, magnitude=1.0, novelty=1.0, source_credibility=1.0, age_hours=0.0),
    ]
    ev = event_impact(members)
    # Symmetric ± cancel → near-zero score and low agreement.
    assert abs(ev.score) < 1e-6
    assert ev.components["agreement"] < 1e-6


def test_event_impact_more_members_more_confidence() -> None:
    one = event_impact([
        article_impact(sentiment=0.5, magnitude=1.0, novelty=1.0, source_credibility=1.0, age_hours=0.0)
    ])
    many = event_impact([
        article_impact(sentiment=0.5, magnitude=1.0, novelty=1.0, source_credibility=1.0, age_hours=0.0)
        for _ in range(8)
    ])
    assert many.confidence > one.confidence


def test_impact_dataclass_shape() -> None:
    imp = Impact(0.5, "bullish", 0.5, 0.4, {})
    assert imp.score == 0.5
    assert imp.direction == "bullish"
    assert imp.magnitude == 0.5
    assert imp.confidence == 0.4
