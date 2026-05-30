"""Article quality scoring from structural signals.

``article_quality`` rates an individual article in ``[0, 1]`` from cheap,
language-agnostic **structural** signals — completeness and form, *not* veracity
or viewpoint. It is a presentation/trust prior for ranking; it does not claim to
judge whether an article is *true*. The optional ``source_credibility`` input
lets a trusted outlet lift, and an unproven one temper, the structural estimate.

Signals & rationale
--------------------
Six structural terms plus the source prior, each in ``[0, 1]``, combined as a
weighted sum (weights in :data:`WEIGHTS`, sum to 1.0):

==================  ======  ==========================================================
component           weight  meaning
==================  ======  ==========================================================
length              0.25    word-count "sweet spot": full articles read best. A
                            plateau curve scores ~1.0 across ``[600, 1500]`` words and
                            penalises stubs (<120) and bloated/scraped pages (>4000).
source_credibility  0.22    the outlet's credibility prior (defaults to a neutral 0.5
                            when unknown), so trusted sources lift quality.
has_published_at    0.13    a real publication date — datable, citable, datelineable.
title_quality       0.13    headline form: sane length, not SHOUTING, not clickbait
                            punctuation (see :func:`_title_quality`).
language_confidence 0.12    detector confidence that the body is coherent text in one
                            language (garbled/mixed extraction scores low).
has_author          0.10    a named byline — accountability.
duplicate_penalty   0.05    ``1 - near_duplicate`` — near-duplicates of already-seen
                            content add little; a small demerit, not a veto.
==================  ======  ==========================================================

The composite is monotonic in each good signal and clamped to ``[0, 1]``.

``numpy``-free: plain arithmetic, no new deps.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from newskoo.models.article import Article

# ── blend weights (sum to 1.0) ───────────────────────────────────────────────────
WEIGHTS: dict[str, float] = {
    "length": 0.25,  # word-count sweet-spot curve — headline structural signal
    "source_credibility": 0.22,  # the outlet's credibility prior
    "has_published_at": 0.13,  # datable / citable
    "title_quality": 0.13,  # headline form (length / caps / clickbait)
    "language_confidence": 0.12,  # coherent monolingual body
    "has_author": 0.10,  # named byline → accountability
    "duplicate_penalty": 0.05,  # mild demerit for near-duplicate content
}

# Word-count sweet spot: full credit on the plateau, ramped penalties outside it.
_LEN_HARD_MIN = 30  # below this ⇒ ~0 (a fragment, not an article)
_LEN_SOFT_MIN = 120  # full penalty clears here (a short but real item)
_LEN_PLATEAU_LO = 600  # ideal range lower bound (full credit)
_LEN_PLATEAU_HI = 1500  # ideal range upper bound (full credit)
_LEN_SOFT_MAX = 4000  # above this the long-form penalty begins
_LEN_HARD_MAX = 12000  # at/above this ⇒ floor (likely concatenated / scraped junk)
# Floor the length term never drops below (a long or tiny article isn't worthless).
_LEN_FLOOR = 0.15

# Neutral source-credibility prior when none is supplied / derivable.
_DEFAULT_SOURCE_CRED = 0.5

# Title-quality tuning.
_TITLE_MIN_CHARS = 15  # shorter than this reads as a stub headline
_TITLE_IDEAL_LO = 30  # comfortable headline length lower bound
_TITLE_IDEAL_HI = 90  # comfortable headline length upper bound
_TITLE_MAX_CHARS = 160  # beyond this it's a paragraph, not a headline
_CLICKBAIT_RE = re.compile(r"[!?]{1}")
_LETTERS_RE = re.compile(r"[^\W\d_]", re.UNICODE)


def _ramp(x: float, lo: float, hi: float) -> float:
    """Linear ramp from 0 at ``lo`` to 1 at ``hi`` (clamped); 1 if ``lo >= hi``."""
    if hi <= lo:
        return 1.0
    return min(1.0, max(0.0, (x - lo) / (hi - lo)))


def _length_score(word_count: int) -> float:
    """Sweet-spot word-count curve in ``[_LEN_FLOOR, 1]``.

    Ramps up from the hard minimum to the soft minimum, sits at 1.0 across the
    ``[600, 1500]`` plateau, then ramps down past the soft maximum to a floor at
    the hard maximum. Continuous and monotonic on each side of the plateau, so a
    600-word article scores higher than both a 30-word and an 8000-word one.
    """
    n = max(0, int(word_count))
    if n <= _LEN_HARD_MIN:
        return _LEN_FLOOR * _ramp(n, 0, _LEN_HARD_MIN)
    if n < _LEN_PLATEAU_LO:
        # Below the plateau: floor + ramp from soft-min up to the plateau.
        rise = _ramp(n, _LEN_HARD_MIN, _LEN_SOFT_MIN)  # clears the stub zone
        approach = _ramp(n, _LEN_SOFT_MIN, _LEN_PLATEAU_LO)
        return _LEN_FLOOR + (1.0 - _LEN_FLOOR) * (0.5 * rise + 0.5 * approach)
    if n <= _LEN_PLATEAU_HI:
        return 1.0
    if n <= _LEN_SOFT_MAX:
        # Gentle, mostly-full credit for legitimate long-form.
        return 1.0 - 0.15 * _ramp(n, _LEN_PLATEAU_HI, _LEN_SOFT_MAX)
    # Beyond the soft max: ramp down toward the floor (scraped/concatenated text).
    decline = _ramp(n, _LEN_SOFT_MAX, _LEN_HARD_MAX)
    return max(_LEN_FLOOR, 0.85 - (0.85 - _LEN_FLOOR) * decline)


def _title_quality(title: str) -> float:
    """Headline-form quality in ``[0, 1]`` from length, caps and clickbait punct.

    Rewards a comfortable length, penalises near-empty or paragraph-length
    titles, ALLCAPS shouting, and excessive ``!``/``?`` punctuation. Heuristic,
    language-agnostic on length/caps; punctuation cues are English/Latin-centric.
    """
    t = (title or "").strip()
    if not t:
        return 0.0
    length = len(t)

    # Length term: ramp in to the ideal band, full credit inside it, ramp out.
    if length < _TITLE_IDEAL_LO:
        length_term = _ramp(length, _TITLE_MIN_CHARS, _TITLE_IDEAL_LO)
    elif length <= _TITLE_IDEAL_HI:
        length_term = 1.0
    else:
        length_term = 1.0 - _ramp(length, _TITLE_IDEAL_HI, _TITLE_MAX_CHARS)

    # Caps term: fraction of letters that are uppercase; shouting is penalised.
    letters = [c for c in t if _LETTERS_RE.match(c)]
    if letters:
        upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
        # Tolerate normal capitalisation (~<35%); ramp the penalty in above that.
        caps_term = 1.0 - _ramp(upper_ratio, 0.35, 0.85)
    else:
        caps_term = 1.0

    # Clickbait punctuation: density of !/? characters.
    bangs = len(_CLICKBAIT_RE.findall(t))
    punct_term = 1.0 - min(1.0, bangs / 3.0)

    # Geometric-ish mean so any single bad cue meaningfully pulls the title down.
    return float(length_term * (0.5 + 0.5 * caps_term) * (0.5 + 0.5 * punct_term))


@dataclass(frozen=True)
class ArticleFeatures:
    """Pre-extracted structural features for :func:`article_quality`."""

    word_count: int
    has_author: bool
    has_published_at: bool
    language_confidence: float  # detector confidence in [0, 1]
    title: str
    near_duplicate: float  # near-duplicate likelihood in [0, 1] (1 = certain dup)
    source_credibility: float | None = None  # outlet prior; neutral 0.5 if None


def _components(features: ArticleFeatures) -> dict[str, float]:
    """Squash each feature into ``[0, 1]`` (see module docstring)."""
    source_cred = (
        _DEFAULT_SOURCE_CRED
        if features.source_credibility is None
        else min(1.0, max(0.0, features.source_credibility))
    )
    return {
        "length": _length_score(features.word_count),
        "source_credibility": source_cred,
        "has_published_at": 1.0 if features.has_published_at else 0.0,
        "title_quality": _title_quality(features.title),
        "language_confidence": min(1.0, max(0.0, features.language_confidence)),
        "has_author": 1.0 if features.has_author else 0.0,
        "duplicate_penalty": 1.0 - min(1.0, max(0.0, features.near_duplicate)),
    }


def article_quality(features: ArticleFeatures) -> float:
    """Composite article quality in ``[0, 1]`` (higher = better structured).

    Weighted sum of the seven normalised components (see :data:`WEIGHTS`).
    Monotonic in each good signal; clamped to ``[0, 1]``.
    """
    components = _components(features)
    score = sum(WEIGHTS[name] * value for name, value in components.items())
    return float(min(1.0, max(0.0, score)))


def quality_components(features: ArticleFeatures) -> dict[str, float]:
    """Per-component normalised breakdown (pre-weight) for explainability/UI."""
    return {name: round(value, 6) for name, value in _components(features).items()}


def _language_confidence(article: Article) -> float:
    """Best-effort language confidence in ``[0, 1]`` from the article row.

    The parse stage may stash a detector probability under
    ``status``-adjacent metadata; absent that, presence of a language code is a
    weak positive (0.7) and a missing code is neutral-low (0.3). Kept simple and
    deterministic — richer confidence can be threaded through later.
    """
    return 0.7 if article.language else 0.3


async def score_article(
    session: AsyncSession,
    article_id: int,
    *,
    source_credibility: float | None = None,
) -> float:
    """Load an :class:`Article`, derive structural features, return its quality.

    Word count, authors, published date, language and simhash come straight off
    the row. ``near_duplicate`` is treated as 0.0 here (cluster-level dedup owns
    cross-article duplication; pass a precomputed value through
    :class:`ArticleFeatures` if you have one). ``source_credibility`` overrides
    the neutral prior when supplied (e.g. from :func:`compute_source_scores`).

    Returns ``0.0`` if the article does not exist. Read-only: no flush/commit.
    """
    article = await session.get(Article, article_id)
    if article is None:
        return 0.0

    features = ArticleFeatures(
        word_count=int(article.word_count or 0),
        has_author=bool(article.authors),
        has_published_at=article.published_at is not None,
        language_confidence=_language_confidence(article),
        title=article.title or "",
        near_duplicate=0.0,
        source_credibility=source_credibility,
    )
    return article_quality(features)


__all__ = [
    "WEIGHTS",
    "ArticleFeatures",
    "article_quality",
    "quality_components",
    "score_article",
]
