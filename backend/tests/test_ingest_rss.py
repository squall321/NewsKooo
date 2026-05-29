"""RSS connector tests + emit_raw RawDocument construction.

``respx`` mocks the feed HTTP; a fake RateLimiter/sleep keep the politeness
engine offline; a fake producer captures published RawDocuments.
"""

from __future__ import annotations

from datetime import UTC
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
import respx
from newskoo.core.contracts import FetchMethod, RawDocument, Topic
from newskoo.ingest.politeness import PolitenessEngine
from newskoo.ingest.producer import build_raw_document, emit_raw
from newskoo.ingest.rss import RssConnector, normalize_entry

FEED_URL = "https://feed.test/rss.xml"

RSS_BODY = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Feed Test</title>
    <item>
      <title>First Story</title>
      <link>https://feed.test/articles/first</link>
      <guid>https://feed.test/articles/first</guid>
      <description>&lt;p&gt;Summary one&lt;/p&gt;</description>
      <pubDate>Mon, 26 May 2026 09:00:00 GMT</pubDate>
      <author>jane@feed.test (Jane Doe)</author>
    </item>
    <item>
      <title>Second Story</title>
      <link>https://feed.test/articles/second</link>
      <description>Summary two</description>
      <pubDate>Tue, 27 May 2026 10:30:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

ATOM_BODY = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Atom Test</title>
  <entry>
    <title>Atom Story</title>
    <link href="https://atom.test/a/1" rel="alternate"/>
    <id>tag:atom.test,2026:1</id>
    <summary>An atom summary</summary>
    <content type="html">&lt;p&gt;Atom body&lt;/p&gt;</content>
    <updated>2026-05-28T12:00:00Z</updated>
    <author><name>Atom Author</name></author>
  </entry>
</feed>
"""


class FakeRateLimiter:
    async def allow(self, domain: str, rate: float, capacity: float = 1.0) -> bool:
        return True


class FakeProducer:
    """Captures (topic, payload, key) tuples passed by kafka.publish()."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, Any, bytes | None]] = []

    async def send_and_wait(self, topic: str, value: Any, *, key: bytes | None = None) -> None:
        self.sent.append((topic, value, key))


def _engine() -> PolitenessEngine:
    async def _sleep(_secs: float) -> None:
        return None

    return PolitenessEngine(
        rate_limiter=FakeRateLimiter(),  # type: ignore[arg-type]
        user_agents=["UA-Test/1.0"],
        respect_robots=False,  # skip robots fetch in connector tests
        default_rps=10.0,
        sleep=_sleep,
    )


def _source(**over: Any) -> SimpleNamespace:
    base = {
        "id": 7,
        "feed_url": FEED_URL,
        "fetch_method": "rss",
        "homepage_url": "https://feed.test/",
        "politeness": {"rps": 5.0},
        "name": "Feed Test",
    }
    base.update(over)
    return SimpleNamespace(**base)


def test_normalize_entry_extracts_fields() -> None:
    import feedparser

    parsed = feedparser.parse(RSS_BODY)
    item = normalize_entry(parsed.entries[0])
    assert item is not None
    assert item["url"] == "https://feed.test/articles/first"
    assert item["canonical_url"] == "https://feed.test/articles/first"
    assert item["title"] == "First Story"
    assert "Summary one" in (item["content"] or "")
    assert "Jane Doe" in item["authors"][0]


@respx.mock
async def test_rss_connector_yields_items() -> None:
    respx.get(FEED_URL).mock(
        return_value=httpx.Response(
            200, text=RSS_BODY, headers={"content-type": "application/rss+xml"}
        )
    )
    conn = RssConnector(engine=_engine())
    items = [item async for item in conn.fetch(_source())]
    assert len(items) == 2
    urls = [i["url"] for i in items]
    assert urls == [
        "https://feed.test/articles/first",
        "https://feed.test/articles/second",
    ]
    assert items[0]["http_status"] == 200
    assert items[0]["content_type"] == "application/rss+xml"


@respx.mock
async def test_rss_connector_parses_atom() -> None:
    url = "https://atom.test/feed.xml"
    respx.get(url).mock(return_value=httpx.Response(200, text=ATOM_BODY))
    conn = RssConnector(engine=_engine())
    items = [item async for item in conn.fetch(_source(feed_url=url))]
    assert len(items) == 1
    assert items[0]["url"] == "https://atom.test/a/1"
    assert items[0]["title"] == "Atom Story"
    assert "Atom body" in (items[0]["content"] or "")


@respx.mock
async def test_rss_connector_handles_304_not_modified() -> None:
    route = respx.get(FEED_URL)
    route.mock(
        return_value=httpx.Response(
            200, text=RSS_BODY, headers={"ETag": '"v1"', "content-type": "application/rss+xml"}
        )
    )
    conn = RssConnector(engine=_engine())
    first = [item async for item in conn.fetch(_source())]
    assert len(first) == 2

    # Second poll: server replies 304; connector must yield nothing.
    route.mock(return_value=httpx.Response(304))
    second = [item async for item in conn.fetch(_source())]
    assert second == []
    # The conditional request carried the cached validator.
    last_request = route.calls.last.request
    assert last_request.headers.get("If-None-Match") == '"v1"'


@respx.mock
async def test_rss_connector_handles_http_error_gracefully() -> None:
    respx.get(FEED_URL).mock(return_value=httpx.Response(500))
    conn = RssConnector(engine=_engine())
    items = [item async for item in conn.fetch(_source())]
    assert items == []


@respx.mock
async def test_rss_connector_handles_transport_error() -> None:
    respx.get(FEED_URL).mock(side_effect=httpx.ConnectError("down"))
    conn = RssConnector(engine=_engine())
    items = [item async for item in conn.fetch(_source())]
    assert items == []


async def test_rss_connector_no_feed_url_yields_nothing() -> None:
    conn = RssConnector(engine=_engine())
    items = [item async for item in conn.fetch(_source(feed_url=None))]
    assert items == []


def test_build_raw_document_maps_fields() -> None:
    item = {
        "url": "https://x.test/a",
        "canonical_url": "https://x.test/a-canonical",
        "title": "Title",
        "content": "<p>body</p>",
        "published": "2026-05-26T09:00:00Z",
        "http_status": 200,
        "content_type": "application/rss+xml",
    }
    doc = build_raw_document(5, item, FetchMethod.RSS)
    assert isinstance(doc, RawDocument)
    assert doc.source_id == 5
    assert doc.canonical_url == "https://x.test/a-canonical"
    assert doc.raw_html == "<p>body</p>"
    assert doc.title_hint == "Title"
    assert doc.fetch_method == FetchMethod.RSS
    assert doc.published_at_hint is not None
    assert doc.published_at_hint.tzinfo is not None
    assert doc.fetched_at.tzinfo == UTC


def test_build_raw_document_requires_url() -> None:
    with pytest.raises(ValueError):
        build_raw_document(1, {"title": "no url"}, FetchMethod.RSS)


async def test_emit_raw_publishes_keyed_by_canonical_url() -> None:
    producer = FakeProducer()
    item = {
        "url": "https://x.test/a",
        "canonical_url": "https://x.test/canon",
        "title": "T",
        "content": "<p>b</p>",
    }
    doc = await emit_raw(producer, 9, item, "rss")
    assert len(producer.sent) == 1
    topic, payload, key = producer.sent[0]
    assert topic == str(Topic.RAW_DOCUMENTS)
    assert isinstance(payload, RawDocument)
    assert payload.source_id == 9
    assert key == b"https://x.test/canon"  # canonical preferred over url
    assert doc.canonical_url == "https://x.test/canon"


async def test_emit_raw_falls_back_to_url_key() -> None:
    producer = FakeProducer()
    item = {"url": "https://x.test/only-url", "raw_html": "<p>b</p>"}
    await emit_raw(producer, 1, item, FetchMethod.HTML)
    _, payload, key = producer.sent[0]
    assert key == b"https://x.test/only-url"
    assert payload.fetch_method == FetchMethod.HTML
    assert payload.raw_html == "<p>b</p>"


async def test_rss_emit_integration_builds_valid_documents() -> None:
    """End-to-end: connector items -> emit_raw -> valid RawDocuments."""
    with respx.mock:
        respx.get(FEED_URL).mock(return_value=httpx.Response(200, text=RSS_BODY))
        producer = FakeProducer()
        conn = RssConnector(engine=_engine())
        async for item in conn.fetch(_source()):
            await emit_raw(producer, 7, item, "rss")
        docs = [p for _, p, _ in producer.sent]

    assert len(docs) == 2
    assert all(isinstance(d, RawDocument) for d in docs)
    assert all(d.fetch_method == FetchMethod.RSS for d in docs)
    assert {d.url for d in docs} == {
        "https://feed.test/articles/first",
        "https://feed.test/articles/second",
    }


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
