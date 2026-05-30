"""Blocking keys to keep entity resolution sub-quadratic.

Naive resolution compares a candidate against *every* existing entity — O(n²)
over the catalog and hopeless at scale. *Blocking* (a.k.a. indexing) partitions
entities into overlapping buckets keyed by cheap, match-correlated features; we
then only score candidates that share at least one block key. This trades a
small amount of recall (true matches that share no key are missed) for a large
reduction in comparisons.

We emit three complementary families of keys per name so that a true duplicate
survives at least one of them:

1. **Sorted-token-set key** (``ts:...``) — tokens deduplicated, sorted, and
   joined. Robust to word *reordering* and *repetition*: "Morgan JP" and
   "JP Morgan" share ``ts:jp morgan``. Misses spelling variants and extra/
   missing words. High precision, moderate recall.

2. **First-token + type key** (``ft:<type>:<tok>``) — the leading token plus the
   entity type. Cheap, groups "Apple Inc"/"Apple Records" together for scoring
   (the matcher then separates them). Recovers cases the sorted-set key misses
   because of trailing-word differences. Lower precision, higher recall — and
   the type qualifier keeps unrelated types out of the same bucket.

3. **Trigram + prefix keys** (``tg:<3>``, ``px:<4>``) — character 3-grams of the
   collapsed (space-free) key, plus a 4-char prefix. These survive *spelling*
   variation and minor typos ("Citibank"/"Citybank" share many trigrams) and
   mirror the DB-side ``pg_trgm`` similarity used by :mod:`service`. Highest
   recall, lowest precision; capped to a handful of trigrams to bound fan-out.

Recall/precision tradeoff
-------------------------
More keys (especially trigrams) ⇒ higher recall but bigger candidate sets
(more scoring work, more false candidates to reject). Fewer/stricter keys ⇒
fewer comparisons but more missed matches. The matcher (:mod:`match`) is the
precision backstop: blocking only has to *not miss*; the score gate decides.
The DB path in :mod:`service` reproduces the same intent with ``pg_trgm``
``similarity`` + ``ANY(aliases)`` + token ``ILIKE`` so candidate generation is
pushed into Postgres instead of materialising the whole table.

References
----------
* Christen, P. (2012). *Data Matching*, ch. 4 ("Indexing"), Springer.
* Papadakis et al. (2020), "Blocking and Filtering Techniques for Entity
  Resolution: A Survey", ACM Computing Surveys 53(2).
"""

from __future__ import annotations

from newskoo.resolve.normalize import normalize_name, tokens

# Number of leading character trigrams emitted (bounds candidate fan-out).
_MAX_TRIGRAMS = 4
# Prefix length for the prefix key.
_PREFIX_LEN = 4
# Minimum collapsed-key length before trigram/prefix keys are worthwhile.
_MIN_TRIGRAM_LEN = 3


def _trigram_keys(collapsed: str) -> set[str]:
    """First ``_MAX_TRIGRAMS`` character 3-grams of ``collapsed`` as keys.

    Trigrams are sorted for determinism and de-duplicated; only the leading few
    are kept so a long name does not explode the candidate set. ``collapsed`` is
    the normalized key with spaces removed (so trigrams span word boundaries the
    way ``pg_trgm`` would after its own normalization).
    """
    if len(collapsed) < _MIN_TRIGRAM_LEN:
        return set()
    grams = sorted({collapsed[i : i + 3] for i in range(len(collapsed) - 2)})
    return {f"tg:{g}" for g in grams[:_MAX_TRIGRAMS]}


def block_keys(name: str, type: str) -> set[str]:
    """Return the set of blocking keys for ``name``/``type``.

    Two entities are *candidates* iff their key sets intersect. An empty or
    unnormalizable name yields an empty set (it can match nothing by blocking and
    must be handled as a guaranteed-new entity by the caller).
    """
    key = normalize_name(name, type)
    if not key:
        return set()

    toks = tokens(name)
    keys: set[str] = set()

    # 1. Sorted-token-set key (order/repetition invariant).
    if toks:
        token_set = " ".join(sorted(set(toks)))
        keys.add(f"ts:{token_set}")

        # 2. First-token + type key.
        keys.add(f"ft:{type.casefold()}:{toks[0]}")

    # 3. Trigram + prefix keys over the collapsed canonical key.
    collapsed = key.replace(" ", "")
    keys |= _trigram_keys(collapsed)
    if len(collapsed) >= _PREFIX_LEN:
        keys.add(f"px:{collapsed[:_PREFIX_LEN]}")

    return keys
