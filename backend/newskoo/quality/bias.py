"""Honest, lightweight bias *heuristics* — explicitly NOT ground truth.

This module provides two cheap, deterministic, lexicon-based signals and one
interface (no implementation) for a future model:

* :func:`subjectivity` — how opinionated/emotive a body of text reads, from the
  density of subjective / sensational / hedging marker words.
* :func:`sensationalism` — how "shouty" a headline reads, from ALLCAPS ratio,
  exclamation/question density, and superlatives.
* :class:`LLMStanceHook` — a ``Protocol`` describing a future model-based
  stance/bias call. **No LLM is invoked here.**

What these heuristics DO claim
------------------------------
A rough, surface-level *style* signal useful as a ranking demerit / UI flag /
feature for a downstream classifier. They are monotonic in marker density and
bounded ``[0, 1]``.

What these heuristics DO NOT claim
----------------------------------
* **Not** a measure of political *direction* (left/right) — only intensity of
  subjective/sensational style.
* **Not** a truth/accuracy judgement: a calm article can be false; a heated one
  can be true. Style ≠ veracity.
* **Not** language-complete. The lexicons are **English-centric** (with a few
  common markers); on other languages they degrade to near-zero rather than
  giving a wrong-but-confident answer. Treat non-English scores as low-signal.
* **Not** ground truth — for actual stance/bias use a calibrated model behind
  :class:`LLMStanceHook`, and even then label it as model output.

``numpy``-free, no new deps.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from newskoo.core.accel import normalize

# ── English-centric marker lexicons ─────────────────────────────────────────────
# Subjective / opinion / emotive markers (intensity of editorialising).
_SUBJECTIVE_MARKERS: frozenset[str] = frozenset(
    {
        "amazing", "appalling", "astonishing", "awful", "best", "brilliant",
        "catastrophe", "catastrophic", "chaos", "crazy", "devastating", "disaster",
        "disgrace", "disgraceful", "dreadful", "extraordinary", "fabulous",
        "fantastic", "frightening", "horrible", "horrific", "incredible",
        "insane", "outrage", "outrageous", "perfect", "ridiculous", "scandal",
        "scandalous", "shameful", "shocking", "spectacular", "stunning",
        "terrible", "terrifying", "tragedy", "tragic", "unbelievable",
        "wonderful", "worst",
        # opinion framing
        "clearly", "obviously", "undeniably", "surely", "frankly", "honestly",
        "absurd", "blatant", "must", "should", "shameless",
    }
)
# Hedging / uncertainty markers (epistemic softening — also a subjectivity tell).
_HEDGING_MARKERS: frozenset[str] = frozenset(
    {
        "allegedly", "apparently", "arguably", "could", "likely", "may", "maybe",
        "might", "perhaps", "possibly", "presumably", "probably", "purportedly",
        "reportedly", "seemingly", "supposedly", "claim", "claims", "claimed",
        "rumored", "rumoured", "speculation", "unconfirmed",
    }
)
# Superlatives / absolutes that drive sensational headlines.
_SUPERLATIVE_MARKERS: frozenset[str] = frozenset(
    {
        "best", "worst", "biggest", "smallest", "greatest", "largest", "huge",
        "massive", "ultimate", "epic", "insane", "unbelievable", "shocking",
        "ever", "never", "always", "must", "everyone", "nobody", "secret",
        "exposed", "revealed", "destroyed", "slammed", "explosive",
    }
)

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)
_BANG_RE = re.compile(r"[!?]")
_LETTER_RE = re.compile(r"[^\W\d_]", re.UNICODE)
_WORD_RE = re.compile(r"\b[^\W\d_]{2,}\b", re.UNICODE)

# Saturation constants: density at which the term reaches ~0.5 (then diminishing).
_SUBJ_D50 = 0.06  # ~6% subjective/hedging markers ⇒ mid subjectivity
_SUPERLATIVE_D50 = 0.15  # ~15% superlative tokens in a (short) headline ⇒ mid


def _saturate(value: float, mid: float) -> float:
    """Saturating map ``value / (value + mid)`` to ``[0, 1)``, monotonic.

    Zero at ``value == 0``, 0.5 at ``value == mid``, approaching 1.0 above it
    with diminishing returns. ``mid`` must be > 0.
    """
    v = max(0.0, value)
    return v / (v + mid)


def _tokens(text: str) -> list[str]:
    """Normalised word tokens (NFKC + lowercase via the shared accel facade)."""
    return _TOKEN_RE.findall(normalize(text or ""))


def subjectivity(text: str) -> float:
    """Heuristic subjectivity of ``text`` in ``[0, 1]`` (higher = more opinionated).

    Counts subjective/emotive and hedging marker words, normalises by total token
    count, and saturates the density. Monotonic in marker density. **Heuristic,
    English-centric, not ground truth** — see the module docstring.

    Empty / token-less input returns 0.0.
    """
    toks = _tokens(text)
    if not toks:
        return 0.0
    markers = _SUBJECTIVE_MARKERS | _HEDGING_MARKERS
    hits = sum(1 for t in toks if t in markers)
    density = hits / len(toks)
    return float(_saturate(density, _SUBJ_D50))


def sensationalism(title: str) -> float:
    """Heuristic sensationalism of a ``title`` in ``[0, 1]`` (higher = shoutier).

    Blends three surface cues, each in ``[0, 1]``:

    * **ALLCAPS ratio** — fraction of letters that are uppercase (shouting).
    * **punctuation density** — ``!``/``?`` per word, saturating (clickbait).
    * **superlatives** — share of tokens that are superlative/absolute markers.

    Equal-weighted average. Monotonic in each cue. **Heuristic, English/Latin-
    centric, not ground truth.** Empty input returns 0.0.
    """
    t = (title or "").strip()
    if not t:
        return 0.0

    # ALLCAPS ratio over letters only (ignores digits/punctuation/spaces).
    letters = [c for c in t if _LETTER_RE.match(c)]
    caps_ratio = (
        sum(1 for c in letters if c.isupper()) / len(letters) if letters else 0.0
    )

    words = _WORD_RE.findall(t)
    word_count = max(1, len(words))

    # Exclamation/question density per word, saturated (3 bangs/word ⇒ ~1).
    bangs = len(_BANG_RE.findall(t))
    punct_term = _saturate(bangs / word_count, 0.34)

    # Superlative share among alphabetic tokens.
    toks = _tokens(t)
    if toks:
        superlative_hits = sum(1 for tk in toks if tk in _SUPERLATIVE_MARKERS)
        superlative_term = _saturate(superlative_hits / len(toks), _SUPERLATIVE_D50)
    else:
        superlative_term = 0.0

    return float((caps_ratio + punct_term + superlative_term) / 3.0)


@dataclass(frozen=True)
class StanceResult:
    """Result shape a future :class:`LLMStanceHook` implementation should return.

    Carrier for *model* output only — never produced by the heuristics here.
    ``stance`` is a free-form label (e.g. ``"supportive"`` / ``"critical"`` /
    ``"neutral"``); ``bias_direction`` an optional political lean label;
    ``confidence`` the model's self-reported confidence in ``[0, 1]``;
    ``rationale`` a short human-readable justification.
    """

    stance: str
    confidence: float
    bias_direction: str | None = None
    rationale: str | None = None


@runtime_checkable
class LLMStanceHook(Protocol):
    """Interface for a *future* model-based stance/bias call. **Not implemented.**

    A concrete implementation would call a calibrated classifier or an LLM
    (behind the project's ``LLMProvider`` abstraction) to label an article's
    stance toward its subject and an optional political lean, returning a
    :class:`StanceResult`. The heuristics in this module deliberately do **not**
    attempt this; wire a real implementation in later and label its output as
    model-derived.
    """

    async def stance(
        self, *, title: str, body: str, language: str | None = None
    ) -> StanceResult:
        """Classify stance/bias for one article (to be implemented by a model)."""
        ...


__all__ = [
    "LLMStanceHook",
    "StanceResult",
    "sensationalism",
    "subjectivity",
]
