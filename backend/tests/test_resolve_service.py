"""Service-layer tests against a mocked AsyncSession (no live DB).

The blocking query is simulated: ``execute().scalars().all()`` returns the
synthetic candidate :class:`Entity` rows the test supplies (we do not exercise
pg_trgm). ``session.get`` returns whichever candidate the resolver matched (by
id) so the alias-merge / embedding-backfill path runs. New inserts are captured
via ``session.add`` and assigned an id on ``flush`` (mirroring autoincrement).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from newskoo.models.taxonomy import Entity
from newskoo.resolve.service import resolve_entity


def _session(candidates: list[Entity]) -> AsyncMock:
    """Fake AsyncSession returning ``candidates`` from the blocking query.

    * ``execute()`` → object whose ``.scalars().all()`` is ``candidates``.
    * ``get(Entity, pk)`` → the candidate with that id (for the merge path).
    * ``add`` captures new entities; ``flush`` assigns ids to id-less rows.
    """
    session = AsyncMock()
    by_id = {int(c.id): c for c in candidates if c.id is not None}
    added: list[object] = []
    seq = {"n": max(by_id) if by_id else 0}

    scalars = MagicMock()
    scalars.all.return_value = candidates
    exec_res = MagicMock()
    exec_res.scalars.return_value = scalars
    session.execute = AsyncMock(return_value=exec_res)

    async def _get(model: type, pk: object) -> object | None:
        if model is Entity:
            return by_id.get(int(pk))
        return None

    def _add(obj: object) -> None:
        added.append(obj)

    async def _flush() -> None:
        for obj in added:
            if isinstance(obj, Entity) and getattr(obj, "id", None) is None:
                seq["n"] += 1
                obj.id = seq["n"]
                by_id[obj.id] = obj

    session.get = AsyncMock(side_effect=_get)
    session.add = MagicMock(side_effect=_add)
    session.flush = AsyncMock(side_effect=_flush)
    session.added = added  # type: ignore[attr-defined]
    return session


async def test_picks_right_candidate_and_merges_alias() -> None:
    candidates = [
        Entity(id=1, name="Bank of America", type="org", aliases=["BofA"]),
        Entity(id=2, name="JP Morgan", type="org", aliases=["JPM"]),
    ]
    session = _session(candidates)

    entity_id, is_new = await resolve_entity(
        session, "JPMorgan Chase", "org", threshold=0.75
    )

    assert is_new is False
    assert entity_id == 2
    # The novel surface form "JPMorgan Chase" is merged into the matched entity.
    assert "JPMorgan Chase" in candidates[1].aliases
    # Existing alias preserved, no duplicates.
    assert "JPM" in candidates[1].aliases
    assert len(candidates[1].aliases) == len({a.casefold() for a in candidates[1].aliases})
    # No new Entity inserted on a match.
    assert not any(isinstance(o, Entity) for o in session.added)


async def test_empty_candidates_inserts_new_entity() -> None:
    session = _session([])

    entity_id, is_new = await resolve_entity(
        session,
        "Brand New Co",
        "org",
        aliases=["BNC"],
        embedding=[0.1, 0.2],
        threshold=0.88,
    )

    assert is_new is True
    new_entities = [o for o in session.added if isinstance(o, Entity)]
    assert len(new_entities) == 1
    ent = new_entities[0]
    assert ent.id == entity_id
    assert ent.name == "Brand New Co"
    assert ent.type == "org"
    # The candidate's extra surface form seeds the alias array.
    assert ent.aliases == ["BNC"]
    assert ent.embedding == [0.1, 0.2]


async def test_below_threshold_candidate_inserts_new() -> None:
    # A weak partial-overlap candidate must not be merged into.
    candidates = [Entity(id=5, name="Apple Records", type="org", aliases=[])]
    session = _session(candidates)

    entity_id, is_new = await resolve_entity(session, "Apple", "org", threshold=0.88)

    assert is_new is True
    new_entities = [o for o in session.added if isinstance(o, Entity)]
    assert len(new_entities) == 1
    assert new_entities[0].id == entity_id
    # The existing candidate is untouched.
    assert candidates[0].aliases == []


async def test_embedding_backfilled_on_match_when_missing() -> None:
    candidates = [Entity(id=3, name="Samsung Electronics", type="org", aliases=[], embedding=None)]
    session = _session(candidates)

    entity_id, is_new = await resolve_entity(
        session,
        "Samsung Electronics Co., Ltd.",
        "org",
        embedding=[0.5, 0.5],
        threshold=0.80,
    )

    assert is_new is False
    assert entity_id == 3
    # Embedding backfilled because the matched entity had none.
    assert candidates[0].embedding == [0.5, 0.5]
