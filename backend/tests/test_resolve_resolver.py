"""Resolver decision tests: threshold boundary, best-pick, new-alias computation."""

from __future__ import annotations

from newskoo.resolve.match import MatchSide
from newskoo.resolve.resolver import ExistingEntity, resolve


def test_empty_candidates_is_new() -> None:
    cand = MatchSide(name="Acme Corp", type="org")
    decision = resolve(cand, [], threshold=0.88)
    assert decision.is_new is True
    assert decision.matched_id is None
    assert decision.score == 0.0
    assert decision.new_aliases == []


def test_picks_best_scoring_existing_above_threshold() -> None:
    cand = MatchSide(name="JPMorgan Chase", type="org")
    existing = [
        ExistingEntity(id=1, name="Bank of America", type="org"),
        ExistingEntity(id=2, name="JP Morgan", type="org"),
    ]
    decision = resolve(cand, existing, threshold=0.75)
    assert decision.is_new is False
    assert decision.matched_id == 2


def test_threshold_boundary_is_inclusive() -> None:
    cand = MatchSide(name="Acme Corporation", type="org")
    existing = [ExistingEntity(id=7, name="Acme Corporation", type="org")]
    # An identical name scores 1.0; set the threshold exactly there.
    decision = resolve(cand, existing, threshold=1.0)
    assert decision.is_new is False
    assert decision.matched_id == 7
    assert decision.score == 1.0

    # Just above the achievable score → NEW.
    s = decision.score
    strict = resolve(cand, existing, threshold=min(1.0, s) + 1e-6 if s < 1.0 else 1.0)
    # When s == 1.0 we cannot exceed it; assert the inclusive case held above.
    if s < 1.0:
        assert strict.is_new is True


def test_below_threshold_is_new() -> None:
    cand = MatchSide(name="Apple", type="org")
    existing = [ExistingEntity(id=3, name="Apple Records", type="org")]
    decision = resolve(cand, existing, threshold=0.88)
    assert decision.is_new is True
    assert decision.matched_id is None
    # The best observed score is still reported even on NEW.
    assert decision.score > 0.0


def test_new_aliases_are_novel_surface_forms_only() -> None:
    cand = MatchSide(
        name="삼성전자",
        type="org",
        aliases=["Samsung Electronics", "Samsung Electronics Co., Ltd."],
    )
    existing = [
        ExistingEntity(
            id=9,
            name="Samsung Electronics",
            type="org",
            aliases=["삼성"],
            embedding=[1.0, 0.05],
        )
    ]
    cand.embedding = [1.0, 0.06]  # near-identical vectors → matches across scripts
    decision = resolve(cand, existing, threshold=0.80)
    assert decision.is_new is False
    assert decision.matched_id == 9
    # "삼성전자" is novel; "Samsung Electronics" already known (its name);
    # "Samsung Electronics Co., Ltd." normalizes to the known key → not novel.
    assert "삼성전자" in decision.new_aliases
    assert "Samsung Electronics" not in decision.new_aliases
    assert "Samsung Electronics Co., Ltd." not in decision.new_aliases


def test_type_mismatch_forces_new() -> None:
    cand = MatchSide(name="Apple", type="product")
    existing = [ExistingEntity(id=1, name="Apple", type="org")]
    decision = resolve(cand, existing, threshold=0.5)
    assert decision.is_new is True
    assert decision.score == 0.0
