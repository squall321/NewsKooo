"""Canonical name normalization for entity resolution.

The resolver compares entity surface forms that arrive from many languages,
outlets, and LLM extractions. Before any similarity is computed we fold each
surface form into a *canonical key* that erases the differences that should
never block a match (case, accents, punctuation, corporate legal suffixes,
whitespace noise) while preserving the differences that carry meaning (the
actual word content, including non-Latin scripts).

Pipeline (applied in order)::

    1. Unicode NFKC normalization     — unify compatibility forms: the "fi"
                                        ligature -> "fi", fullwidth Latin ->
                                        ASCII, circled "1" -> "1", etc.
    2. casefold()                     — aggressive, locale-independent lowering
                                        (handles eszett -> "ss", final-sigma,
                                        dotted/dotless I, ...).
    3. strip combining marks (Mn)     — drop diacritics so "São"→"sao",
                                        "Müller"→"muller", "Beyoncé"→"beyonce".
                                        Done *after* NFKC via an NFD pass so the
                                        base letters survive.
    4. strip legal suffixes (org)     — "Apple Inc." and "Apple" share a key.
    5. collapse punctuation→space     — commas, periods, hyphens, quotes become
                                        separators; runs of space collapse to one.

CJK and Arabic (and any other non-Latin script) pass through untouched: NFKC and
casefold are no-ops or safe for them, the Mn strip only removes *combining*
marks (Arabic harakat are stripped, which is the desired behaviour for matching
unvocalised vs. vocalised forms; base CJK ideographs and Arabic letters carry no
combining class and are preserved).

References
----------
* Unicode Standard Annex #15, "Unicode Normalization Forms" (NFKC/NFD).
* Unicode Standard Annex #29, on text segmentation / combining marks.
* Christen, P. (2012). *Data Matching*, ch. 3 (data pre-processing &
  standardisation for entity resolution).
"""

from __future__ import annotations

import re
import unicodedata

# ── Organisation legal suffixes ───────────────────────────────────────────────
# Lower-cased, punctuation-free tokens (or token n-grams) that denote a legal
# corporate form rather than the entity's identity. They are matched and removed
# only for ``type == "org"`` (and the catch-all "company"/"organization"). The
# set is intentionally multilingual; add cautiously — an over-broad suffix can
# merge distinct entities (precision risk).
_ORG_LEGAL_SUFFIXES: frozenset[str] = frozenset(
    {
        # English / common
        "inc",
        "incorporated",
        "ltd",
        "limited",
        "llc",
        "llp",
        "lp",
        "plc",
        "corp",
        "corporation",
        "co",
        "company",
        "group",
        "holdings",
        "holding",
        # German
        "gmbh",
        "ag",
        "kg",
        "kgaa",
        "mbh",
        "se",
        # Romance
        "sa",  # S.A. (FR/ES/PT/IT) — also Société Anonyme
        "spa",  # S.p.A. (IT)
        "srl",  # S.r.l. (IT)
        "sas",  # S.A.S. (FR)
        "sl",  # S.L. (ES)
        "sarl",
        # Dutch / Nordic
        "nv",  # N.V.
        "bv",  # B.V.
        "oyj",  # FI public
        "oy",  # FI
        "ab",  # SE
        "asa",  # NO
        "as",  # NO/DK
        "aps",  # DK
        # CJK
        "株式会社",  # kabushiki-gaisha (JP joint-stock)
        "株",  # short form
        "有限会社",  # JP limited
        "有限公司",  # ZH limited
        "股份有限公司",  # ZH joint-stock
        "公司",  # ZH company
        "주식회사",  # KR joint-stock
    }
)

# Multi-token suffixes (checked as joined runs) so "co ltd", "pty ltd",
# "股份 有限 公司" collapse even when whitespace/punct split them.
_ORG_LEGAL_SUFFIX_NGRAMS: tuple[tuple[str, ...], ...] = (
    ("股份", "有限", "公司"),
    ("有限", "公司"),
    ("co", "ltd"),
    ("pty", "ltd"),
    ("co", "ltd", "co"),
)

_ORG_TYPES: frozenset[str] = frozenset({"org", "organization", "organisation", "company"})

# Punctuation / separators → whitespace. Keep letters (any script), marks we
# have not already stripped, and digits. ``\w`` is Unicode-aware in ``re``.
_PUNCT_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
_WS_RE = re.compile(r"\s+", flags=re.UNICODE)
_TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)


def _strip_combining_marks(text: str) -> str:
    """Remove combining marks (Unicode category ``Mn``) after an NFD pass.

    Decomposing to NFD separates base characters from their combining
    diacritics; dropping category-``Mn`` codepoints then yields the unaccented
    base. A final NFC re-composition restores precomposed characters that NFD
    split — crucially **Hangul syllables**, which NFD decomposes into conjoining
    jamo (category ``Lo``, *not* ``Mn``, so they survive the filter); without the
    recompose "삼성" would be left as its constituent jamo and never match the
    precomposed form. Latin diacritics are already gone (their marks are ``Mn``),
    so NFC cannot reattach them. CJK ideographs and Arabic base letters carry no
    combining class and are untouched throughout.
    """
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", stripped)


def _basic_fold(name: str) -> str:
    """NFKC → casefold → strip diacritics → punctuation-to-space → collapse.

    The shared front half of normalization used by every type.
    """
    text = unicodedata.normalize("NFKC", name)
    text = text.casefold()
    text = _strip_combining_marks(text)
    text = _PUNCT_RE.sub(" ", text)
    return _WS_RE.sub(" ", text).strip()


def _strip_org_suffixes(folded: str) -> str:
    """Drop trailing legal-form tokens from an already-folded org name.

    Repeatedly removes any trailing token (or multi-token n-gram) that is a
    known legal suffix, so chains like "Foo Co., Ltd." → "foo". Never strips the
    final remaining token, so a bare suffix-only name (degenerate input) keeps a
    key rather than collapsing to "".
    """
    parts = folded.split()
    if not parts:
        return folded

    # First, fold known multi-token suffix n-grams from the tail.
    changed = True
    while changed and len(parts) > 1:
        changed = False
        for ngram in _ORG_LEGAL_SUFFIX_NGRAMS:
            n = len(ngram)
            if len(parts) > n and tuple(parts[-n:]) == ngram:
                parts = parts[:-n]
                changed = True
                break
        # Then peel single-token suffixes.
        while len(parts) > 1 and parts[-1] in _ORG_LEGAL_SUFFIXES:
            parts = parts[:-1]
            changed = True

    return " ".join(parts)


def normalize_name(name: str, type: str) -> str:
    """Return the canonical match key for ``name`` of the given entity ``type``.

    The key is what blocking and exact-key comparison operate on. Two surface
    forms that *should* be the same entity (modulo case/accents/punctuation/legal
    form) collapse to an identical key.

    * ``org``-like types additionally have legal suffixes stripped, so
      "Apple Inc.", "Apple, Inc" and "APPLE INCORPORATED" → ``"apple"``.
    * ``person`` (and everything else) keeps token order — only spacing, case,
      and diacritics are normalized — so "José Mourinho" → ``"jose mourinho"``
      without reordering given/family names.

    An empty or whitespace-only ``name`` yields ``""``.
    """
    folded = _basic_fold(name)
    if not folded:
        return ""
    if type.casefold() in _ORG_TYPES:
        folded = _strip_org_suffixes(folded)
    return folded


def tokens(name: str) -> list[str]:
    """Tokenize ``name`` into normalized word tokens (script-agnostic).

    Applies the shared NFKC/casefold/diacritic/punctuation fold (but *no* legal-
    suffix stripping — tokenization is type-independent) then splits on Unicode
    word boundaries. CJK runs without spaces collapse to a single token (there is
    no segmentation here by design); callers that need CJW segmentation should do
    it upstream. Returns ``[]`` for empty input.
    """
    folded = _basic_fold(name)
    if not folded:
        return []
    return _TOKEN_RE.findall(folded)
