"""Bias-heuristic tests: subjectivity & sensationalism bounds and ordering.

These assert the heuristics behave as *style* signals (sensational/clickbait
text scores high; neutral factual text scores low) — they do NOT assert any
truth/stance claim. Pure functions, no DB / network.
"""

from __future__ import annotations

import inspect

from newskoo.quality.bias import (
    LLMStanceHook,
    StanceResult,
    sensationalism,
    subjectivity,
)

_NEUTRAL = "The central bank kept its benchmark interest rate unchanged on Tuesday."
_OPINION = (
    "This is an absolute disaster and a shocking, outrageous scandal; frankly the "
    "worst, most appalling and disgraceful decision anyone could possibly imagine."
)
_NEUTRAL_TITLE = "Central bank holds interest rate steady in May"
_CLICKBAIT_TITLE = "SHOCKING!!! You WON'T BELIEVE This INSANE Secret EXPOSED!!!"


def test_subjectivity_bounded() -> None:
    for text in (_NEUTRAL, _OPINION, "", "   "):
        assert 0.0 <= subjectivity(text) <= 1.0


def test_subjectivity_opinion_beats_neutral() -> None:
    assert subjectivity(_OPINION) > subjectivity(_NEUTRAL)
    assert subjectivity(_NEUTRAL) < 0.2
    assert subjectivity(_OPINION) > 0.5


def test_subjectivity_empty_is_zero() -> None:
    assert subjectivity("") == 0.0
    assert subjectivity("12345 67890") == 0.0  # no word tokens after digits-only


def test_subjectivity_monotonic_in_marker_density() -> None:
    filler = " ".join(["the report covers the quarter"] * 6)
    none = filler
    few = filler + " shocking"
    many = filler + " shocking outrageous disaster scandal appalling"
    assert subjectivity(none) <= subjectivity(few) <= subjectivity(many)


def test_sensationalism_bounded() -> None:
    for title in (_NEUTRAL_TITLE, _CLICKBAIT_TITLE, "", "   "):
        assert 0.0 <= sensationalism(title) <= 1.0


def test_sensationalism_clickbait_beats_neutral() -> None:
    assert sensationalism(_CLICKBAIT_TITLE) > sensationalism(_NEUTRAL_TITLE)
    assert sensationalism(_NEUTRAL_TITLE) < 0.2
    assert sensationalism(_CLICKBAIT_TITLE) > 0.5


def test_sensationalism_allcaps_drives_score() -> None:
    plain = "Markets close higher after earnings"
    shouting = "MARKETS CLOSE HIGHER AFTER EARNINGS"
    assert sensationalism(shouting) > sensationalism(plain)


def test_sensationalism_exclamation_density_increases_score() -> None:
    calm = "Company reports quarterly earnings"
    excited = "Company reports quarterly earnings!!!"
    assert sensationalism(excited) > sensationalism(calm)


def test_sensationalism_empty_is_zero() -> None:
    assert sensationalism("") == 0.0


def test_stance_hook_is_protocol_not_implemented() -> None:
    # The hook is an interface only — Protocol with an abstract async method.
    assert hasattr(LLMStanceHook, "stance")
    assert inspect.iscoroutinefunction(LLMStanceHook.stance)
    # It is a runtime-checkable Protocol; a plain object does not satisfy it.
    assert not isinstance(object(), LLMStanceHook)


def test_stance_result_shape() -> None:
    result = StanceResult(stance="neutral", confidence=0.5)
    assert result.stance == "neutral"
    assert result.confidence == 0.5
    assert result.bias_direction is None
