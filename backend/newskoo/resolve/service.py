"""Async DB integration for entity resolution.

This is the stateful counterpart to the pure :mod:`resolver`. It replaces the
naive exact-``(name, type)`` upsert in :mod:`newskoo.storage.results` with a
fuzzy, multilingual, alias-aware resolution:

    candidate (name, type, aliases?, embedding?)
        │
        ├─ generate candidates via *blocking pushed into Postgres*:
        │     type filter
        │     AND ( pg_trgm  similarity(name, :q) > k     -- fuzzy name match
        │           OR :q = ANY(aliases)                  -- known alias hit
        │           OR name ILIKE :first_token            -- shared leading token
        │           OR aliases && :alias_array )          -- alias intersection
        │
        ├─ score each candidate with :func:`match.score`
        ├─ decide with :func:`resolver.resolve` (threshold = entity_match_threshold)
        │
        ├─ MATCH → merge novel surface forms into ``Entity.aliases`` (deduped),
        │          backfill ``Entity.embedding`` if it was NULL, return (id, False)
        └─ NEW   → insert a fresh ``Entity`` (aliases = candidate's surface forms,
                   embedding if given), return (new_id, True)

Transaction discipline mirrors the rest of the storage layer: we ``flush`` so
the row gets an ``id`` and is visible to later queries in the same unit of work,
but we never ``commit`` — the worker's ``session_scope`` owns the transaction.

The pg_trgm similarity cutoff ``k`` is derived from ``entity_match_threshold``
but kept deliberately *looser* (``k = threshold * _TRGM_RECALL_FACTOR``): blocking
must over-generate (favour recall); the precise decision is the matcher's job.
"""

from __future__ import annotations

from sqlalchemy import ColumnElement, String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from newskoo.core.config import get_settings
from newskoo.core.logging import get_logger
from newskoo.models.taxonomy import Entity
from newskoo.resolve import resolver
from newskoo.resolve.match import MatchSide
from newskoo.resolve.normalize import tokens

log = get_logger(__name__)

# Blocking should recall more than the decision threshold accepts, so the trigram
# cutoff is the threshold scaled down. Clamped so it never drops below a sane floor.
_TRGM_RECALL_FACTOR: float = 0.45
_TRGM_MIN: float = 0.15
# Cap candidates fetched per resolution (bounds fan-out / scoring cost).
_CANDIDATE_LIMIT: int = 50


def _dedupe_preserving_order(values: list[str]) -> list[str]:
    """Drop empties and case-insensitive duplicates, keep first-seen spelling."""
    seen: set[str] = set()
    out: list[str] = []
    for v in values:
        if not v or not v.strip():
            continue
        key = v.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(v)
    return out


async def _fetch_candidates(
    session: AsyncSession,
    name: str,
    type_: str,
    aliases: list[str],
    *,
    trgm_cutoff: float,
) -> list[resolver.ExistingEntity]:
    """Blocking query: type-filtered, fuzzy/alias/token-overlapping candidates.

    Uses ``pg_trgm``'s ``similarity()`` for fuzzy name matching, ``= ANY(aliases)``
    for exact alias hits, an ``ILIKE`` on the leading token for shared-prefix
    recall, and array overlap (``&&``) when the candidate brings its own aliases.
    Type-permissive rows (blank/``unknown``) are *not* excluded so the matcher's
    permissive-type rule still applies.
    """
    name_toks = tokens(name)
    first_token = name_toks[0] if name_toks else name

    # ``Entity.aliases`` maps the *base* ``sqlalchemy.ARRAY`` (per the frozen
    # taxonomy model), whose typed comparator does not implement ``contains``/
    # ``&&``; we therefore build the PostgreSQL array predicates with ``.op()``
    # and ``func.any``, which the base ``ColumnElement`` supports.
    conditions: list[ColumnElement[bool]] = [
        func.similarity(Entity.name, name) > trgm_cutoff,
        cast(name, String) == func.any(Entity.aliases),  # name = ANY(aliases)
        Entity.name.ilike(f"%{first_token}%"),
    ]
    if aliases:
        # aliases && ARRAY[...] — any of the candidate's aliases already known?
        conditions.append(Entity.aliases.op("&&")(cast(aliases, Entity.aliases.type)))

    type_ok = or_(
        Entity.type == type_,
        Entity.type == "",
        Entity.type == "unknown",
    )

    stmt = (
        select(Entity)
        .where(type_ok, or_(*conditions))
        .order_by(func.similarity(Entity.name, cast(name, String)).desc())
        .limit(_CANDIDATE_LIMIT)
    )
    res = await session.execute(stmt)
    rows = res.scalars().all()
    return [
        resolver.ExistingEntity(
            id=int(e.id),
            name=e.name,
            type=e.type,
            aliases=list(e.aliases or []),
            embedding=list(e.embedding) if e.embedding is not None else None,
        )
        for e in rows
    ]


async def resolve_entity(
    session: AsyncSession,
    name: str,
    type: str,
    *,
    aliases: list[str] | None = None,
    embedding: list[float] | None = None,
    threshold: float | None = None,
) -> tuple[int, bool]:
    """Resolve (and persist) an entity surface form to a canonical ``Entity``.

    Fetches blocking candidates, scores them, and either merges into the best
    match or inserts a new entity. Returns ``(entity_id, is_new)``.

    On MATCH: novel surface forms (the candidate's name/aliases the entity does
    not already know) are appended to ``Entity.aliases`` (deduped), and a missing
    ``Entity.embedding`` is backfilled from ``embedding`` if provided.

    On NEW: inserts an ``Entity`` whose ``aliases`` are the candidate's extra
    surface forms (its name minus itself) and ``embedding`` is ``embedding``.

    Flushes (so the id is assigned and visible) but never commits.
    """
    settings = get_settings()
    thr = settings.entity_match_threshold if threshold is None else threshold
    trgm_cutoff = max(_TRGM_MIN, thr * _TRGM_RECALL_FACTOR)
    incoming_aliases = _dedupe_preserving_order(list(aliases or []))

    candidates = await _fetch_candidates(
        session, name, type, incoming_aliases, trgm_cutoff=trgm_cutoff
    )

    cand_side = MatchSide(
        name=name,
        type=type,
        aliases=list(incoming_aliases),
        embedding=embedding,
    )
    decision = resolver.resolve(cand_side, candidates, threshold=thr)

    if not decision.is_new and decision.matched_id is not None:
        entity = await session.get(Entity, decision.matched_id)
        if entity is not None:
            if decision.new_aliases:
                merged = _dedupe_preserving_order([*(entity.aliases or []), *decision.new_aliases])
                entity.aliases = merged
            if entity.embedding is None and embedding is not None:
                entity.embedding = list(embedding)
            await session.flush()
            log.info(
                "resolve.matched",
                entity_id=entity.id,
                name=name,
                type=type,
                score=round(decision.score, 4),
                added_aliases=len(decision.new_aliases),
            )
            return int(entity.id), False
        # Matched id vanished (race) — fall through to insert a fresh entity.
        log.warning("resolve.matched_missing", matched_id=decision.matched_id, name=name)

    # NEW: the candidate's *extra* surface forms (aliases excluding the name) seed
    # the alias array.
    new_aliases = _dedupe_preserving_order(
        [a for a in incoming_aliases if a.casefold() != name.casefold()]
    )
    entity = Entity(
        name=name,
        type=type,
        aliases=new_aliases,
        embedding=list(embedding) if embedding is not None else None,
    )
    session.add(entity)
    await session.flush()
    log.info(
        "resolve.new",
        entity_id=entity.id,
        name=name,
        type=type,
        best_score=round(decision.score, 4),
    )
    return int(entity.id), True
