"""Phase-7 API tests — no live DB/Kafka required.

Strategy: build the app via ``create_app()``, override the ``db_session``
dependency with a fake :class:`AsyncSession` whose ``execute``/``scalar`` return
canned results, and drive it with ``httpx.AsyncClient`` over an
``ASGITransport``. Each test installs the exact fakes the route under test needs.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from newskoo.api.deps import db_session
from newskoo.api.main import create_app
from newskoo.core.config import get_settings
from newskoo.models.source import Source


# ── Fake-session plumbing ────────────────────────────────────────────────────
def _scalars_result(values: list[Any]) -> MagicMock:
    """A result object whose ``.scalars().all()`` yields ``values``."""
    res = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = values
    res.scalars.return_value = scalars
    return res


def _rows_result(rows: list[Any]) -> MagicMock:
    """A result object whose ``.all()`` yields ``rows`` (Row-like tuples/objs)."""
    res = MagicMock()
    res.all.return_value = rows
    return res


def make_fake_session(
    *,
    execute_results: list[Any] | None = None,
    scalar_results: list[Any] | None = None,
    get_result: Any = None,
) -> AsyncMock:
    """Construct a fake AsyncSession.

    - ``execute`` returns each item of ``execute_results`` in order (then repeats
      the last), so tests can script the per-query results a route issues.
    - ``scalar`` likewise walks ``scalar_results`` (used for COUNT(*) etc.).
    - ``get`` returns ``get_result``.
    """
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.get = AsyncMock(return_value=get_result)

    exec_seq = list(execute_results or [])

    async def _execute(*_a: Any, **_k: Any) -> Any:
        if not exec_seq:
            return _rows_result([])
        return exec_seq[0] if len(exec_seq) == 1 else exec_seq.pop(0)

    scalar_seq = list(scalar_results or [])

    async def _scalar(*_a: Any, **_k: Any) -> Any:
        if not scalar_seq:
            return 0
        return scalar_seq[0] if len(scalar_seq) == 1 else scalar_seq.pop(0)

    session.execute = AsyncMock(side_effect=_execute)
    session.scalar = AsyncMock(side_effect=_scalar)
    return session


def client_with_session(session: AsyncMock) -> AsyncClient:
    """Build an app with ``db_session`` overridden to yield ``session``."""
    app = create_app()

    async def _override():
        yield session

    app.dependency_overrides[db_session] = _override
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


def _sample_source(**over: Any) -> Source:
    defaults: dict[str, Any] = {
        "id": 1,
        "name": "Example",
        "homepage_url": "https://example.test/",
        "feed_url": "https://example.test/rss.xml",
        "api_kind": None,
        "fetch_method": "rss",
        "region": "US",
        "languages": ["en"],
        "categories": ["general"],
        "bot_sensitivity": 0,
        "politeness": {"rps": 1.0},
        "robots_url": None,
        "enabled": True,
        "health": {},
    }
    defaults.update(over)
    return Source(**defaults)


# ── /health ──────────────────────────────────────────────────────────────────
async def test_health() -> None:
    session = make_fake_session()
    async with client_with_session(session) as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "newskoo-api"


# ── /metrics ──────────────────────────────────────────────────────────────────
async def test_metrics_endpoint() -> None:
    session = make_fake_session()
    async with client_with_session(session) as client:
        # Hit a route first so the request counter has a sample to export.
        await client.get("/health")
        resp = await client.get("/metrics")
    assert resp.status_code == 200
    assert "newskoo_http_requests_total" in resp.text


# ── /api/sources list shape + pagination ─────────────────────────────────────
async def test_list_sources_shape_and_pagination() -> None:
    rows = [_sample_source(id=1), _sample_source(id=2, name="Two")]
    session = make_fake_session(
        execute_results=[_scalars_result(rows)],  # list_sources query
        scalar_results=[2],  # count
    )
    async with client_with_session(session) as client:
        resp = await client.get("/api/sources?limit=10&offset=0&enabled=true")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body) == {"items", "total", "limit", "offset"}
    assert body["total"] == 2
    assert body["limit"] == 10
    assert body["offset"] == 0
    assert len(body["items"]) == 2
    assert body["items"][0]["id"] == 1
    assert body["items"][0]["name"] == "Example"


async def test_get_source_404() -> None:
    session = make_fake_session(get_result=None)
    async with client_with_session(session) as client:
        resp = await client.get("/api/sources/999")
    assert resp.status_code == 404


# ── /api/search fts branch ───────────────────────────────────────────────────
async def test_search_fts_returns_results() -> None:
    art = MagicMock()
    art.id = 7
    art.source_id = 1
    art.canonical_url = "https://example.test/a"
    art.url = "https://example.test/a"
    art.title = "Big news"
    art.body = "body text"
    art.language = "en"
    art.authors = []
    art.published_at = datetime(2026, 5, 1, tzinfo=UTC)
    art.fetched_at = datetime(2026, 5, 1, tzinfo=UTC)
    art.word_count = 2
    art.status = "analyzed"
    art.event_id = None

    # FTS route issues one execute → list of (Article, rank) rows.
    session = make_fake_session(execute_results=[_rows_result([(art, 0.95)])])
    async with client_with_session(session) as client:
        resp = await client.post(
            "/api/search",
            json={"q": "big news", "mode": "fts", "limit": 5},
        )
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["id"] == 7
    assert results[0]["title"] == "Big news"
    assert results[0]["score"] == pytest.approx(0.95)
    # FTS must not require the embedding provider.
    session.execute.assert_awaited()


# ── /api/trends shape ────────────────────────────────────────────────────────
async def test_trends_shape() -> None:
    point = MagicMock()
    point.bucket = datetime(2026, 5, 29, 10, tzinfo=UTC)
    point.count = 12
    point.source_count = 4
    point.velocity = 1.5
    point.zscore = 3.2

    # First execute → series rows; second execute → label scalar.
    session = make_fake_session(execute_results=[_rows_result([point])])
    session.scalar = AsyncMock(return_value="OpenAI")  # _label_for
    async with client_with_session(session) as client:
        resp = await client.get(
            "/api/trends?target_type=entity&target_id=42&window=48"
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["target_type"] == "entity"
    assert body["target_id"] == 42
    assert body["label"] == "OpenAI"
    assert len(body["points"]) == 1
    pt = body["points"][0]
    assert pt["count"] == 12
    assert pt["velocity"] == pytest.approx(1.5)
    assert pt["zscore"] == pytest.approx(3.2)


async def test_trends_requires_target_or_keyword() -> None:
    session = make_fake_session()
    async with client_with_session(session) as client:
        resp = await client.get("/api/trends?target_type=topic")
    assert resp.status_code == 422


# ── auth: mutation 401 without key when configured ───────────────────────────
async def test_mutation_requires_api_key_when_configured() -> None:
    get_settings.cache_clear()
    import os

    os.environ["NEWSKOO_API_KEY"] = "secret-key"
    try:
        session = make_fake_session()
        payload = {
            "name": "New",
            "homepage_url": "https://new.test/",
            "feed_url": "https://new.test/rss.xml",
            "fetch_method": "rss",
        }
        # Simulate the DB assigning a PK on flush so SourceOut (id: int) validates.
        added: list[Source] = []
        session.add = MagicMock(side_effect=added.append)

        async def _flush_assigns_id() -> None:
            # Mimic what a real INSERT/flush does: assign the PK and apply the
            # column-level defaults (jsonb/array) that aren't set on a transient.
            for obj in added:
                if getattr(obj, "id", None) is None:
                    obj.id = 123
                if getattr(obj, "health", None) is None:
                    obj.health = {}

        session.flush = AsyncMock(side_effect=_flush_assigns_id)

        async with client_with_session(session) as client:
            # No header → 401.
            resp = await client.post("/api/sources", json=payload)
            assert resp.status_code == 401
            # Correct header → passes auth, creates, returns the ORM row.
            ok = await client.post(
                "/api/sources", json=payload, headers={"X-API-Key": "secret-key"}
            )
            assert ok.status_code == 201
            body = ok.json()
            assert body["name"] == "New"
            assert body["id"] == 123
    finally:
        os.environ.pop("NEWSKOO_API_KEY", None)
        get_settings.cache_clear()


async def test_reports_generate_503_when_generator_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POST /api/reports returns 503 when the report generator is unavailable."""
    from newskoo.api.routers import reports as reports_router

    monkeypatch.setattr(reports_router, "_load_generator", lambda: None)
    session = make_fake_session()
    async with client_with_session(session) as client:
        resp = await client.post(
            "/api/reports", json={"keywords": ["ai"], "window": 24}
        )
    # Generator forced unavailable → 503 (not 500/auth, since api_key unset).
    assert resp.status_code == 503


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
