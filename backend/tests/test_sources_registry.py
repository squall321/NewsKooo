"""Registry CRUD + health tests against a mocked AsyncSession (no live DB)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from newskoo.models.source import Source
from newskoo.sources import registry
from newskoo.sources.schemas import SourceCreate, SourceUpdate


def _make_session() -> AsyncMock:
    """A fake AsyncSession: add() records, flush()/get()/execute() are async."""
    session = AsyncMock()
    session.add = MagicMock()  # add is sync on a real Session
    session.flush = AsyncMock()
    return session


def _result_scalar(value: object) -> MagicMock:
    res = MagicMock()
    res.scalar_one_or_none.return_value = value
    return res


def _result_list(values: list[object]) -> MagicMock:
    res = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = values
    res.scalars.return_value = scalars
    return res


async def test_create_source_defaults_politeness_from_bot_sensitivity() -> None:
    session = _make_session()
    payload = SourceCreate(
        name="X",
        homepage_url="https://x.test/",
        feed_url="https://x.test/rss.xml",
        fetch_method="rss",
        region="US",
        languages=["en"],
        categories=["general"],
        bot_sensitivity=2,
    )
    src = await registry.create_source(session, payload)
    session.add.assert_called_once()
    session.flush.assert_awaited()
    assert src.politeness  # auto-filled
    assert src.politeness["max_concurrency"] == 1  # tier-2 default
    assert src.fetch_method == "rss"


async def test_get_by_feed_or_home_prefers_feed_url() -> None:
    session = _make_session()
    found = Source(name="Y", homepage_url="https://y.test/", fetch_method="rss")
    session.execute = AsyncMock(return_value=_result_scalar(found))
    out = await registry.get_by_feed_or_home(
        session, feed_url="https://y.test/rss.xml", homepage_url="https://y.test/"
    )
    assert out is found
    session.execute.assert_awaited_once()  # matched on feed_url, no fallback query


async def test_get_by_feed_or_home_falls_back_to_homepage() -> None:
    session = _make_session()
    found = Source(name="Z", homepage_url="https://z.test/", fetch_method="html")
    # First call (feed_url) -> None; second call (homepage) -> found.
    session.execute = AsyncMock(
        side_effect=[_result_scalar(None), _result_scalar(found)]
    )
    out = await registry.get_by_feed_or_home(
        session, feed_url="https://z.test/rss.xml", homepage_url="https://z.test/"
    )
    assert out is found
    assert session.execute.await_count == 2


async def test_update_source_applies_only_set_fields() -> None:
    session = _make_session()
    existing = Source(
        name="Old",
        homepage_url="https://o.test/",
        fetch_method="rss",
        enabled=True,
        region="US",
    )
    session.get = AsyncMock(return_value=existing)
    out = await registry.update_source(
        session, 1, SourceUpdate(name="New", enabled=False)
    )
    assert out is existing
    assert existing.name == "New"
    assert existing.enabled is False
    assert existing.region == "US"  # untouched


async def test_update_source_missing_returns_none() -> None:
    session = _make_session()
    session.get = AsyncMock(return_value=None)
    out = await registry.update_source(session, 999, SourceUpdate(name="x"))
    assert out is None


async def test_set_enabled_toggles() -> None:
    session = _make_session()
    existing = Source(
        name="S", homepage_url="https://s.test/", fetch_method="rss", enabled=True
    )
    session.get = AsyncMock(return_value=existing)
    out = await registry.set_enabled(session, 1, False)
    assert out is existing
    assert existing.enabled is False


async def test_record_health_merges_counters_and_ring_buffer() -> None:
    session = _make_session()
    existing = Source(
        name="H", homepage_url="https://h.test/", fetch_method="rss", health={}
    )
    session.get = AsyncMock(return_value=existing)

    await registry.record_health(session, 1, ok=True, latency_ms=120.0)
    assert existing.health["total"] == 1
    assert existing.health["fails"] == 0
    assert existing.health["error_rate"] == 0.0
    assert existing.health["last_latency_ms"] == 120.0
    assert "last_ok_at" in existing.health
    assert len(existing.health["recent"]) == 1

    await registry.record_health(session, 1, ok=False, latency_ms=999.0, error="timeout")
    assert existing.health["total"] == 2
    assert existing.health["fails"] == 1
    assert existing.health["error_rate"] == 0.5
    assert existing.health["last_error"] == "timeout"
    assert len(existing.health["recent"]) == 2


async def test_record_health_ring_buffer_capped() -> None:
    session = _make_session()
    existing = Source(
        name="H2", homepage_url="https://h2.test/", fetch_method="rss", health={}
    )
    session.get = AsyncMock(return_value=existing)
    for i in range(30):
        await registry.record_health(session, 1, ok=True, latency_ms=float(i))
    assert len(existing.health["recent"]) == 20  # capped at _HEALTH_HISTORY
    assert existing.health["total"] == 30


async def test_upsert_creates_when_absent() -> None:
    session = _make_session()
    session.execute = AsyncMock(return_value=_result_scalar(None))
    payload = SourceCreate(
        name="New Source",
        homepage_url="https://new.test/",
        feed_url="https://new.test/rss.xml",
        fetch_method="rss",
    )
    out = await registry.upsert_source(session, payload)
    session.add.assert_called_once()
    assert out.name == "New Source"


async def test_upsert_updates_existing_and_preserves_enabled() -> None:
    session = _make_session()
    existing = Source(
        name="Stale Name",
        homepage_url="https://e.test/",
        feed_url="https://e.test/rss.xml",
        fetch_method="rss",
        enabled=False,  # operationally disabled; must survive an upsert
        health={"total": 5},
    )
    session.execute = AsyncMock(return_value=_result_scalar(existing))
    payload = SourceCreate(
        name="Fresh Name",
        homepage_url="https://e.test/",
        feed_url="https://e.test/rss.xml",
        fetch_method="rss",
        categories=["business"],
    )
    out = await registry.upsert_source(session, payload)
    assert out is existing
    assert existing.name == "Fresh Name"  # descriptive fields refreshed
    assert existing.categories == ["business"]
    assert existing.enabled is False  # preserved
    assert existing.health == {"total": 5}  # preserved
    session.add.assert_not_called()


async def test_list_sources_builds_filtered_query() -> None:
    session = _make_session()
    rows = [Source(name="A", homepage_url="https://a.test/", fetch_method="rss")]
    session.execute = AsyncMock(return_value=_result_list(rows))
    out = await registry.list_sources(
        session, enabled=True, region="US", category="science", limit=10
    )
    assert out == rows
    session.execute.assert_awaited_once()


def test_source_create_rejects_rss_without_feed_url() -> None:
    with pytest.raises(ValueError):
        SourceCreate(
            name="bad", homepage_url="https://b.test/", fetch_method="rss"
        )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
