"""API connector tests: GDELT JSON parsing (respx-mocked) and NewsAPI behavior
including the no-key no-op. Settings are overridden per-test by clearing the
cached singleton and patching env-driven flags directly.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import httpx
import pytest
import respx
from newskoo.core.config import get_settings
from newskoo.ingest.api import (
    GDELT_DOC_API,
    NEWSAPI_BASE,
    ApiConnector,
    normalize_gdelt,
    normalize_newsapi,
)
from newskoo.ingest.politeness import PolitenessEngine


class FakeRateLimiter:
    async def allow(self, domain: str, rate: float, capacity: float = 1.0) -> bool:
        return True


def _engine() -> PolitenessEngine:
    async def _sleep(_secs: float) -> None:
        return None

    return PolitenessEngine(
        rate_limiter=FakeRateLimiter(),  # type: ignore[arg-type]
        user_agents=["UA-Test/1.0"],
        respect_robots=False,
        default_rps=10.0,
        sleep=_sleep,
    )


def _source(**over: Any) -> SimpleNamespace:
    base = {
        "id": 3,
        "fetch_method": "api",
        "api_kind": "gdelt",
        "homepage_url": "https://gdelt.test/",
        "feed_url": None,
        "politeness": {},
        "name": "API Source",
    }
    base.update(over)
    return SimpleNamespace(**base)


@pytest.fixture(autouse=True)
def _reset_settings() -> Any:
    """Each test starts from a fresh settings singleton."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


GDELT_JSON = {
    "articles": [
        {
            "url": "https://news.example/a",
            "title": "Global Story A",
            "seendate": "20260526T090000Z",
            "domain": "news.example",
            "language": "English",
            "sourcecountry": "United States",
        },
        {
            "url": "https://news.example/b",
            "title": "Global Story B",
            "seendate": "20260526T100000Z",
        },
        {"url": "", "title": "no url, dropped"},
    ]
}


def test_normalize_gdelt_carries_hints() -> None:
    item = normalize_gdelt(GDELT_JSON["articles"][0])
    assert item is not None
    assert item["url"] == "https://news.example/a"
    assert item["title"] == "Global Story A"
    assert item["headers"]["x-gdelt-domain"] == "news.example"
    assert item["headers"]["x-gdelt-language"] == "English"


def test_normalize_gdelt_skips_urlless() -> None:
    assert normalize_gdelt({"title": "x"}) is None


@respx.mock
async def test_gdelt_connector_yields_items() -> None:
    respx.get(GDELT_DOC_API).mock(return_value=httpx.Response(200, json=GDELT_JSON))
    conn = ApiConnector(engine=_engine())
    items = [item async for item in conn.fetch(_source(api_kind="gdelt"))]
    assert [i["url"] for i in items] == [
        "https://news.example/a",
        "https://news.example/b",
    ]
    assert items[0]["http_status"] == 200


@respx.mock
async def test_gdelt_query_params_from_source() -> None:
    route = respx.get(GDELT_DOC_API).mock(
        return_value=httpx.Response(200, json={"articles": []})
    )
    src = _source(politeness={"api": {"query": "semiconductors", "max_records": 10}})
    conn = ApiConnector(engine=_engine())
    _ = [item async for item in conn.fetch(src)]
    request = route.calls.last.request
    assert request.url.params["query"] == "semiconductors"
    assert request.url.params["maxrecords"] == "10"
    assert request.url.params["format"] == "json"


@respx.mock
async def test_gdelt_handles_http_error() -> None:
    respx.get(GDELT_DOC_API).mock(return_value=httpx.Response(503))
    conn = ApiConnector(engine=_engine())
    items = [item async for item in conn.fetch(_source(api_kind="gdelt"))]
    assert items == []


async def test_gdelt_disabled_yields_nothing() -> None:
    settings = get_settings()
    settings.gdelt_enabled = False
    conn = ApiConnector(engine=_engine())
    items = [item async for item in conn.fetch(_source(api_kind="gdelt"))]
    assert items == []


def test_normalize_newsapi() -> None:
    article = {
        "url": "https://na.example/1",
        "title": "NA Title",
        "description": "desc",
        "content": "trunc...",
        "publishedAt": "2026-05-26T09:00:00Z",
        "author": "Reporter",
    }
    item = normalize_newsapi(article)
    assert item is not None
    assert item["url"] == "https://na.example/1"
    assert item["authors"] == ["Reporter"]
    assert item["summary"] == "desc"


async def test_newsapi_no_key_is_noop() -> None:
    settings = get_settings()
    settings.newsapi_key = ""  # explicit: no credentials
    conn = ApiConnector(engine=_engine())
    items = [item async for item in conn.fetch(_source(api_kind="newsapi"))]
    assert items == []


@respx.mock
async def test_newsapi_with_key_yields_items() -> None:
    settings = get_settings()
    settings.newsapi_key = "secret-key"
    payload = {
        "status": "ok",
        "articles": [
            {"url": "https://na.example/1", "title": "One", "publishedAt": "2026-05-26T00:00:00Z"},
            {"url": "https://na.example/2", "title": "Two", "publishedAt": "2026-05-26T01:00:00Z"},
        ],
    }
    route = respx.get(f"{NEWSAPI_BASE}/everything").mock(
        return_value=httpx.Response(200, json=payload)
    )
    conn = ApiConnector(engine=_engine())
    items = [item async for item in conn.fetch(_source(api_kind="newsapi"))]
    assert [i["url"] for i in items] == ["https://na.example/1", "https://na.example/2"]
    # API key passed via header, not query string.
    assert route.calls.last.request.headers.get("X-Api-Key") == "secret-key"


@respx.mock
async def test_newsapi_error_status_yields_nothing() -> None:
    settings = get_settings()
    settings.newsapi_key = "k"
    respx.get(f"{NEWSAPI_BASE}/everything").mock(
        return_value=httpx.Response(200, json={"status": "error", "message": "rate limited"})
    )
    conn = ApiConnector(engine=_engine())
    items = [item async for item in conn.fetch(_source(api_kind="newsapi"))]
    assert items == []


async def test_api_unknown_kind_yields_nothing() -> None:
    conn = ApiConnector(engine=_engine())
    items = [item async for item in conn.fetch(_source(api_kind="mystery"))]
    assert items == []


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
