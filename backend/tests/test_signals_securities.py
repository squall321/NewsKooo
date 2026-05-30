"""Security seed catalog + entity→security linking tests.

The seed list is validated structurally (no DB). Linking is exercised against
the pure matcher (:func:`_best_match`) and against a mocked ``AsyncSession`` for
the full :func:`link_entities_to_securities` path (no live DB / pg_trgm).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from newskoo.models.finance import EntitySecurity, Security
from newskoo.models.taxonomy import Entity
from newskoo.signals.securities import (
    SECURITIES,
    _best_match,
    _normalize,
    link_entities_to_securities,
    seed_securities,
)

_VALID_ASSET_CLASSES = {"equity", "etf", "index", "adr", "crypto"}


# ── Seed catalog structure ────────────────────────────────────────────────────
def test_seed_has_at_least_120() -> None:
    assert len(SECURITIES) >= 120


def test_seed_symbols_unique() -> None:
    symbols = [s["symbol"] for s in SECURITIES]
    assert len(symbols) == len(set(symbols))


def test_seed_fields_valid() -> None:
    for spec in SECURITIES:
        assert spec["symbol"] and isinstance(spec["symbol"], str)
        assert spec["name"] and isinstance(spec["name"], str)
        assert spec["asset_class"] in _VALID_ASSET_CLASSES
        assert isinstance(spec["aliases"], list)
        # country is ISO-ish (<=8) or None (crypto); exchange present.
        assert spec.get("country") is None or len(spec["country"]) <= 8
        assert "exchange" in spec


def test_seed_covers_required_examples() -> None:
    symbols = {s["symbol"] for s in SECURITIES}
    for required in (
        "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "JPM",
        "TSM", "BABA", "SPY", "QQQ", "^GSPC", "^IXIC",
        "005930.KS", "7203.T",
    ):
        assert required in symbols, f"missing required seed symbol {required}"


def test_seed_has_multiple_asset_classes() -> None:
    classes = {s["asset_class"] for s in SECURITIES}
    assert {"equity", "etf", "index", "adr"} <= classes


# ── Normalization ─────────────────────────────────────────────────────────────
def test_normalize_strips_legal_suffix_and_accents() -> None:
    assert _normalize("Apple Inc.") == "apple"
    assert _normalize("Nestlé S.A.") == "nestle"
    assert _normalize("The Goldman Sachs Group, Inc.") == "goldman sachs"


# ── Pure matcher ──────────────────────────────────────────────────────────────
def _secs() -> list[Security]:
    return [
        Security(id=1, symbol="AAPL", name="Apple Inc.", asset_class="equity", aliases=["Apple"]),
        Security(id=2, symbol="7203.T", name="Toyota Motor Corporation", asset_class="equity", aliases=["Toyota"]),
        Security(id=3, symbol="JPM", name="JPMorgan Chase & Co.", asset_class="equity", aliases=["JPMorgan", "JP Morgan"]),
    ]


def test_apple_inc_matches_aapl_high_confidence() -> None:
    ent = Entity(id=10, name="Apple Inc.", type="org", aliases=[])
    match = _best_match(ent, _secs())
    assert match is not None
    sec, conf = match
    assert sec.symbol == "AAPL"
    assert conf >= 0.95


def test_toyota_matches_japan_listing() -> None:
    ent = Entity(id=11, name="Toyota", type="org", aliases=[])
    match = _best_match(ent, _secs())
    assert match is not None
    sec, conf = match
    assert sec.symbol == "7203.T"
    assert conf >= 0.90


def test_ticker_entity_matches_by_symbol() -> None:
    ent = Entity(id=12, name="AAPL", type="ticker", aliases=[])
    match = _best_match(ent, _secs())
    assert match is not None
    sec, conf = match
    assert sec.symbol == "AAPL"
    assert conf == 1.0


def test_unrelated_entity_no_match() -> None:
    ent = Entity(id=13, name="Springfield Elementary School", type="org", aliases=[])
    assert _best_match(ent, _secs()) is None


def test_fuzzy_name_variant_matches() -> None:
    # "JPMorgan Chase" (no "& Co.") should still link to JPM via fuzzy/alias.
    ent = Entity(id=14, name="JPMorgan Chase", type="org", aliases=[])
    match = _best_match(ent, _secs())
    assert match is not None
    assert match[0].symbol == "JPM"


# ── Full async linking against a mocked session ───────────────────────────────
def _link_session(securities: list[Security], entities: list[Entity]) -> AsyncMock:
    """Mock AsyncSession: ``execute`` returns securities / entities / [] links by
    the model selected, ``add``/``flush`` capture inserts."""
    session = AsyncMock()
    added: list[object] = []

    def _result(rows: list[object]) -> MagicMock:
        scalars = MagicMock()
        scalars.all.return_value = rows
        res = MagicMock()
        res.scalars.return_value = scalars
        return res

    async def _execute(stmt: object) -> MagicMock:
        text = str(stmt)
        if "securities" in text and "entity_securities" not in text:
            return _result(list(securities))
        if "entities" in text and "entity_securities" not in text:
            return _result(list(entities))
        return _result([])  # existing entity_securities links

    session.execute = AsyncMock(side_effect=_execute)
    session.add = MagicMock(side_effect=added.append)
    session.flush = AsyncMock()
    session.added = added  # type: ignore[attr-defined]
    return session


async def test_link_entities_writes_links() -> None:
    securities = _secs()
    entities = [
        Entity(id=100, name="Apple Inc.", type="org", aliases=[]),
        Entity(id=101, name="Toyota", type="org", aliases=[]),
        Entity(id=102, name="Some Random Charity", type="org", aliases=[]),
        Entity(id=103, name="Barack Obama", type="person", aliases=[]),  # skipped (not linkable)
    ]
    session = _link_session(securities, entities)

    written = await link_entities_to_securities(session)

    links = [o for o in session.added if isinstance(o, EntitySecurity)]
    by_entity = {link.entity_id: link for link in links}
    # Apple + Toyota link; the charity and the person do not.
    assert 100 in by_entity
    assert by_entity[100].security_id == 1
    assert by_entity[100].confidence >= 0.95
    assert 101 in by_entity
    assert by_entity[101].security_id == 2
    assert 102 not in by_entity
    assert 103 not in by_entity  # person filtered before matching
    assert written == len(links)


async def test_seed_securities_inserts_when_empty() -> None:
    session = _link_session([], [])
    count = await seed_securities(session)
    inserted = [o for o in session.added if isinstance(o, Security)]
    assert count == len(SECURITIES)
    assert len(inserted) == len(SECURITIES)
    # Symbols round-trip onto the inserted rows.
    assert {s.symbol for s in inserted} == {spec["symbol"] for spec in SECURITIES}
