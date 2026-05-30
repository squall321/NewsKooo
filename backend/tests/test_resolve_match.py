"""Match-scoring tests: string blend, type gate, alias bonus, embedding boost."""

from __future__ import annotations

from newskoo.resolve.match import (
    W_ALIAS,
    W_EMBED,
    W_STRING,
    MatchSide,
    score,
)


def test_weights_are_well_formed() -> None:
    # Strings carry the full-weight base; alias/embedding are residual boosts in (0,1).
    assert W_STRING == 1.0
    assert 0.0 < W_ALIAS < 1.0
    assert 0.0 < W_EMBED < 1.0


def test_jpmorgan_variants_score_high() -> None:
    # "JPMorgan Chase" vs "JP Morgan": a spacing/concatenation variant plus one
    # extra word. Pure string similarity (no alias help) tops out around ~0.78 —
    # comfortably "high" and well separated from a partial overlap like
    # Apple/Apple Records (see below), but not a near-1.0 identity.
    a = MatchSide(name="JPMorgan Chase", type="org")
    b = MatchSide(name="JP Morgan", type="org")
    s = score(a, b)
    assert s >= 0.75
    # And clearly above an unrelated org pair.
    assert s > score(a, MatchSide(name="Bank of America", type="org"))


def test_apple_org_vs_apple_records_lower_than_self() -> None:
    apple = MatchSide(name="Apple", type="org")
    records = MatchSide(name="Apple Records", type="org")
    s_partial = score(apple, records)
    s_self = score(apple, MatchSide(name="Apple Inc.", type="org"))
    assert s_partial < s_self
    # And the partial overlap is meaningfully below a confident match.
    assert s_partial < 0.88


def test_different_types_gate_to_zero() -> None:
    a = MatchSide(name="Apple", type="org")
    b = MatchSide(name="Apple", type="product")
    assert score(a, b) == 0.0


def test_permissive_type_does_not_gate() -> None:
    a = MatchSide(name="Apple", type="org")
    b = MatchSide(name="Apple", type="unknown")
    assert score(a, b) > 0.5


def test_alias_overlap_raises_score() -> None:
    # Surface names differ, but a shared alias signals identity.
    a = MatchSide(name="Alphabet", type="org", aliases=["GOOGL"])
    without = MatchSide(name="Google", type="org")
    with_alias = MatchSide(name="Google", type="org", aliases=["GOOGL"])
    assert score(a, with_alias) > score(a, without)


def test_embedding_boost_rescues_cross_language_pair() -> None:
    # Lexically disjoint across scripts, but multilingual vectors are close.
    korean = MatchSide(name="삼성전자", type="org", embedding=[1.0, 0.05, 0.0])
    english_close = MatchSide(
        name="Samsung Electronics", type="org", embedding=[1.0, 0.06, 0.0]
    )
    english_far = MatchSide(
        name="Samsung Electronics", type="org", embedding=[0.0, 1.0, 0.0]
    )

    s_no_embed = score(
        MatchSide(name="삼성전자", type="org"),
        MatchSide(name="Samsung Electronics", type="org"),
    )
    s_close = score(korean, english_close)
    s_far = score(korean, english_far)

    # With no embeddings the cross-language pair is essentially unmatchable.
    assert s_no_embed < 0.2
    # Close vectors lift it over the merge threshold; far vectors do not.
    assert s_close > s_no_embed
    assert s_close > s_far
    assert s_close >= 0.88


def test_score_bounded_in_unit_interval() -> None:
    a = MatchSide(name="Acme Corporation", type="org", embedding=[2.0, 2.0])
    b = MatchSide(name="Acme Corp", type="org", embedding=[2.0, 2.0])
    s = score(a, b)
    assert 0.0 <= s <= 1.0
