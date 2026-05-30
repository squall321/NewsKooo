"""Pairwise entity-match scoring in [0, 1].

Given two entity *sides* (a freshly extracted candidate and an existing catalog
entity) this module produces a single similarity score that the decision layer
(:mod:`resolver`) thresholds. The score blends complementary signals so no
single string quirk dominates:

Signals
-------
* **String similarity** over normalized names, a convex blend of four RapidFuzz
  metrics that fail in different ways (so no single quirk dominates):

  - ``token_sort_ratio`` — order-invariant after sorting tokens; *penalizes
    extra/missing words*, which is what separates "Apple" from "Apple Records".
  - ``WRatio`` — RapidFuzz's weighted composite; robust to partial overlap and
    length differences ("JP Morgan" vs "JPMorgan Chase & Co").
  - ``JaroWinkler`` — rewards a shared prefix; good for typos and truncations
    ("Citibank"/"Citybank").
  - ``collapsed_ratio`` — plain ``ratio`` on the *space-stripped* names; this is
    the signal that recognises **concatenation/spacing variants** such as
    "JPMorgan" ↔ "JP Morgan" (token metrics treat them as different tokens).

  We deliberately *omit* ``token_set_ratio``: it returns 1.0 whenever one name's
  tokens are a subset of the other's, so it scores "Apple" vs "Apple Records" a
  perfect 1.0 — destroying the very distinction we need. Each metric is mapped
  to [0, 1] and combined with ``_STR_SUBWEIGHTS``.

* **Type gate** — entities of different types are *not* the same entity.
  A mismatch hard-zeros the score (``return 0.0``); "Apple" (org) and "Apple"
  (product) never merge here. Empty/``unknown`` types are treated permissively
  (they do not gate).

* **Alias overlap bonus** — additive credit when the two sides share known
  surface forms (Jaccard over the union of name plus aliases, normalized). A firm
  signal of identity that raw name similarity can miss (e.g. ticker vs full
  name listed as each other's alias).

* **Embedding cosine boost** *(cross-language path)* — when *both* sides carry an
  embedding, blend in cosine similarity. This is what unifies entities whose
  surface forms do not align lexically across scripts/languages
  ("삼성전자" ↔ "Samsung Electronics"): string metrics are near-zero but the
  multilingual embeddings are close. Cosine in [-1, 1] is clamped to [0, 1].

Final score
-----------
Let ``s`` = string score, ``a`` = alias Jaccard, ``e`` = clamped cosine
(only when both embeddings present). Both the alias and embedding terms are
**residual boosts** — each closes the remaining gap to 1.0 in proportion to its
signal, so neither can ever *lower* the lexical base::

    base  = W_STRING * s                              # = s, full-weight strings
    base += W_ALIAS  * a * (1 - base)                 # alias-overlap bonus
    score = base                                      (no embeddings)
    score = base + W_EMBED * e * (1 - base)           (both embeddings present)

Properties that make the residual-boost shape right here:

* identical names score ``s = 1`` ⇒ ``base = 1`` with no alias/embedding help;
* a strong string match is never diluted by the absence of shared aliases
  (the old convex blend penalised name-only matches by ``W_ALIAS``);
* a distant vector (``e ≈ 0``) leaves the score untouched, so a coincidental
  lexical neighbour is not falsely confirmed and a contradictory-type pair is
  still gated to 0 (the type gate runs first);
* a close vector (``e ≈ 1``) can carry a lexically *disjoint* cross-language
  pair ("삼성전자" ↔ "Samsung Electronics", ``s ≈ 0``) over the merge threshold —
  the entire purpose of the embedding signal.

All weights are module constants and documented inline.

References
----------
* Winkler, W. E. (1990). "String Comparator Metrics ... Record Linkage".
* Cohen, Ravikumar, Fienberg (2003). "A Comparison of String Distance Metrics
  for Name-Matching Tasks", IIWeb.
* RapidFuzz docs — ``fuzz.token_set_ratio`` / ``fuzz.WRatio`` /
  ``distance.JaroWinkler``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np
from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler

from newskoo.resolve.normalize import normalize_name

# ── Sub-weights of the string-similarity blend (sum to 1.0) ───────────────────
# Tuned on a labelled mini-suite (JPMorgan/JP Morgan, Apple/Apple Records,
# Acme Corp, Citibank/Citybank) for maximal separation between true and partial
# matches; see tests/test_resolve_match.py.
_STR_SUBWEIGHTS: dict[str, float] = {
    "token_sort_ratio": 0.30,  # word-order normalized; penalizes extra words
    "wratio": 0.30,  # length/partial robustness
    "jaro_winkler": 0.20,  # prefix/typo sensitivity
    "collapsed_ratio": 0.20,  # spacing/concatenation variants (JPMorgan↔JP Morgan)
}

# ── Top-level signal weights ──────────────────────────────────────────────────
# The string-similarity blend carries the lexical base at FULL weight (W_STRING
# == 1.0): two identical names must score 1.0 on strings alone, and a strong
# string match must not be diluted just because the sides list no shared aliases.
W_STRING: float = 1.0
# Alias overlap is an *additive bonus* (not a competing weight): it lifts the
# base toward 1.0 in proportion to the Jaccard of shared surface forms. This is
# what rescues pairs whose displayed names differ but whose alias sets intersect
# (ticker ↔ full name). Capped via the residual ``(1 - base)`` so the total stays
# in [0, 1] and a strong string score is never *lowered*.
W_ALIAS: float = 0.60
# Embedding boost strength. High because cross-language pairs are lexically
# disjoint (``base ≈ 0``); the boost must be able to carry a close-vector pair
# over the merge threshold. Applied as the same residual-boost shape as the alias
# bonus, so a perfect cosine alone yields ``W_EMBED`` (not 1.0), preserving a
# margin of doubt for embedding-only matches.
W_EMBED: float = 0.90

# Types that should never gate a match (unknown/blank are permissive).
_PERMISSIVE_TYPES: frozenset[str] = frozenset({"", "unknown", "misc", "other"})


@dataclass(slots=True)
class MatchSide:
    """One side of a comparison: a name + type, with optional aliases/embedding.

    ``aliases`` are *surface forms* (any language/script); ``embedding`` is the
    multilingual entity vector (same dimensionality on both sides) or ``None``.
    """

    name: str
    type: str
    aliases: list[str] = field(default_factory=list)
    embedding: Sequence[float] | None = None


def _norm_surface_set(side: MatchSide) -> set[str]:
    """Normalized set of name plus aliases for ``side`` (empty keys dropped)."""
    forms = {side.name, *side.aliases}
    out = {normalize_name(f, side.type) for f in forms}
    out.discard("")
    return out


def _string_score(name_a: str, name_b: str) -> float:
    """Convex blend of the four RapidFuzz metrics over normalized names → [0,1]."""
    tsort = fuzz.token_sort_ratio(name_a, name_b) / 100.0
    wr = fuzz.WRatio(name_a, name_b) / 100.0
    jw = JaroWinkler.similarity(name_a, name_b)  # already in [0, 1]
    collapsed = fuzz.ratio(name_a.replace(" ", ""), name_b.replace(" ", "")) / 100.0
    return (
        _STR_SUBWEIGHTS["token_sort_ratio"] * tsort
        + _STR_SUBWEIGHTS["wratio"] * wr
        + _STR_SUBWEIGHTS["jaro_winkler"] * jw
        + _STR_SUBWEIGHTS["collapsed_ratio"] * collapsed
    )


def _alias_jaccard(a: MatchSide, b: MatchSide) -> float:
    """Jaccard overlap of the two normalized surface-form sets → [0, 1]."""
    set_a = _norm_surface_set(a)
    set_b = _norm_surface_set(b)
    if not set_a or not set_b:
        return 0.0
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union else 0.0


def _cosine(u: Sequence[float], v: Sequence[float]) -> float:
    """Cosine similarity of two equal-length vectors → [-1, 1] (0 if degenerate)."""
    a = np.asarray(u, dtype=np.float64)
    b = np.asarray(v, dtype=np.float64)
    if a.shape != b.shape or a.size == 0:
        return 0.0
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _type_matches(type_a: str, type_b: str) -> bool:
    """True when types are compatible (equal, or either is permissive)."""
    ta = type_a.casefold()
    tb = type_b.casefold()
    if ta in _PERMISSIVE_TYPES or tb in _PERMISSIVE_TYPES:
        return True
    return ta == tb


def score(a: MatchSide, b: MatchSide) -> float:
    """Similarity of two entity sides in ``[0, 1]`` (see module docstring).

    A hard **type gate** runs first: incompatible types return ``0.0``. Otherwise
    the lexical base (full-weight string blend, then the alias-Jaccard residual
    bonus) is computed; if *both* sides carry an embedding, the clamped cosine
    applies a further residual boost via ``W_EMBED`` (the cross-language
    unification path). See the module docstring for the exact formula.
    """
    if not _type_matches(a.type, b.type):
        return 0.0

    s = _string_score(normalize_name(a.name, a.type), normalize_name(b.name, b.type))
    # Full-weight lexical base, then the alias-overlap residual bonus.
    base = W_STRING * s
    alias = _alias_jaccard(a, b)
    base = base + W_ALIAS * alias * (1.0 - base)

    if a.embedding is not None and b.embedding is not None:
        cos = _cosine(a.embedding, b.embedding)
        cos01 = max(0.0, min(1.0, cos))  # clamp [-1,1] → [0,1]
        # Multiplicative residual boost: close the gap to 1.0 by W_EMBED * cosine.
        base = base + W_EMBED * cos01 * (1.0 - base)

    return max(0.0, min(1.0, base))
