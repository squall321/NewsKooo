"""Entity resolution / multilingual unification.

Replaces the naive exact-``(name, type)`` entity upsert with fuzzy, alias-aware,
cross-language resolution. Layers:

* :mod:`normalize` — canonical match keys + tokenization (NFKC/casefold/diacritic
  strip/legal-suffix strip).
* :mod:`blocking`  — sub-quadratic candidate keys (sorted-token-set, first-token,
  trigram/prefix).
* :mod:`match`     — pairwise score in [0, 1]: RapidFuzz string blend + type gate
  + alias-overlap bonus + optional embedding-cosine boost (cross-language).
* :mod:`resolver`  — pure MATCH/NEW decision over fetched candidates.
* :mod:`service`   — async DB integration (``resolve_entity``): pg_trgm/alias/token
  blocking → score → decide → merge aliases / backfill embedding / insert.

Typical caller (the storage/analyze stage)::

    from newskoo.resolve import resolve_entity
    entity_id, is_new = await resolve_entity(
        session, name, type_, aliases=aliases, embedding=embedding
    )
"""

from __future__ import annotations

from newskoo.resolve.blocking import block_keys
from newskoo.resolve.match import (
    W_ALIAS,
    W_EMBED,
    W_STRING,
    MatchSide,
    score,
)
from newskoo.resolve.normalize import normalize_name, tokens
from newskoo.resolve.resolver import (
    ExistingEntity,
    ResolveDecision,
    resolve,
)
from newskoo.resolve.service import resolve_entity

__all__ = [
    "W_ALIAS",
    "W_EMBED",
    "W_STRING",
    "ExistingEntity",
    "MatchSide",
    "ResolveDecision",
    "block_keys",
    "normalize_name",
    "resolve",
    "resolve_entity",
    "score",
    "tokens",
]
