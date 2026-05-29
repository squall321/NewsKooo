"""Discovery tests — RSS autodiscovery (respx-mocked HTTP), sitemap & OPML.

No live network: ``respx`` intercepts httpx; XML parsing is offline.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from newskoo.sources.discovery import (
    discover_feeds,
    extract_feed_links,
    import_opml,
    parse_sitemap,
    parse_sitemap_xml,
)

HOMEPAGE = "https://example-news.test/"

HTML_WITH_FEED = """
<!doctype html>
<html>
  <head>
    <title>Example News</title>
    <link rel="alternate" type="application/rss+xml" title="Example RSS"
          href="/feeds/main.xml" />
    <link rel="alternate" type="application/atom+xml" title="Example Atom"
          href="https://example-news.test/atom.xml" />
    <link rel="stylesheet" href="/styles.css" />
  </head>
  <body><h1>Hello</h1></body>
</html>
"""

HTML_NO_FEED = """
<!doctype html><html><head><title>Bare</title></head>
<body><a href="/about">About</a></body></html>
"""

FEED_XML = '<?xml version="1.0"?><rss version="2.0"><channel></channel></rss>'


def test_extract_feed_links_resolves_relative_and_absolute() -> None:
    links = extract_feed_links(HTML_WITH_FEED, HOMEPAGE)
    urls = {link_dict["url"] for link_dict in links}
    assert "https://example-news.test/feeds/main.xml" in urls
    assert "https://example-news.test/atom.xml" in urls
    # The stylesheet must not be treated as a feed.
    assert all("styles.css" not in u for u in urls)
    types = {link_dict["type"] for link_dict in links}
    assert "application/rss+xml" in types


@respx.mock
async def test_discover_feeds_finds_link_alternate() -> None:
    respx.get(HOMEPAGE).mock(
        return_value=httpx.Response(200, html=HTML_WITH_FEED)
    )
    candidates = await discover_feeds(HOMEPAGE, probe_common_paths=False)
    urls = {c["url"] for c in candidates}
    assert "https://example-news.test/feeds/main.xml" in urls
    assert "https://example-news.test/atom.xml" in urls


@respx.mock
async def test_discover_feeds_probes_common_paths_when_none_declared() -> None:
    respx.get(HOMEPAGE).mock(return_value=httpx.Response(200, html=HTML_NO_FEED))
    # /feed responds with a real RSS body; other probes 404.
    respx.get("https://example-news.test/feed").mock(
        return_value=httpx.Response(
            200, text=FEED_XML, headers={"content-type": "application/rss+xml"}
        )
    )
    respx.route(method="GET").mock(return_value=httpx.Response(404))
    candidates = await discover_feeds(HOMEPAGE, probe_common_paths=True)
    urls = {c["url"] for c in candidates}
    assert "https://example-news.test/feed" in urls


@respx.mock
async def test_discover_feeds_handles_homepage_error_gracefully() -> None:
    respx.get(HOMEPAGE).mock(side_effect=httpx.ConnectError("boom"))
    candidates = await discover_feeds(HOMEPAGE, probe_common_paths=False)
    assert candidates == []


def test_parse_sitemap_xml_urlset() -> None:
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://example-news.test/a</loc></url>
      <url><loc>https://example-news.test/b</loc></url>
    </urlset>"""
    parsed = parse_sitemap_xml(xml)
    assert parsed["urls"] == [
        "https://example-news.test/a",
        "https://example-news.test/b",
    ]
    assert parsed["sitemaps"] == []


def test_parse_sitemap_xml_index() -> None:
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <sitemap><loc>https://example-news.test/sm1.xml</loc></sitemap>
    </sitemapindex>"""
    parsed = parse_sitemap_xml(xml)
    assert parsed["sitemaps"] == ["https://example-news.test/sm1.xml"]
    assert parsed["urls"] == []


@respx.mock
async def test_parse_sitemap_follows_index() -> None:
    index_xml = """<?xml version="1.0"?>
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <sitemap><loc>https://example-news.test/sm-child.xml</loc></sitemap>
    </sitemapindex>"""
    child_xml = """<?xml version="1.0"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://example-news.test/story-1</loc></url>
      <url><loc>https://example-news.test/story-2</loc></url>
    </urlset>"""
    respx.get("https://example-news.test/sitemap.xml").mock(
        return_value=httpx.Response(200, text=index_xml)
    )
    respx.get("https://example-news.test/sm-child.xml").mock(
        return_value=httpx.Response(200, text=child_xml)
    )
    urls = await parse_sitemap("https://example-news.test/sitemap.xml")
    assert urls == [
        "https://example-news.test/story-1",
        "https://example-news.test/story-2",
    ]


def test_import_opml_flat_and_nested() -> None:
    opml = """<?xml version="1.0" encoding="UTF-8"?>
    <opml version="2.0">
      <head><title>My feeds</title></head>
      <body>
        <outline text="News">
          <outline type="rss" text="BBC" title="BBC News"
                   xmlUrl="http://feeds.bbci.co.uk/news/rss.xml"/>
          <outline type="rss" text="Guardian"
                   xmlUrl="https://www.theguardian.com/world/rss"/>
        </outline>
        <outline type="rss" text="Folder-less"
                 xmlUrl="https://example-news.test/feed.xml"/>
      </body>
    </opml>"""
    items = import_opml(opml)
    feed_urls = {i["feed_url"] for i in items}
    assert "http://feeds.bbci.co.uk/news/rss.xml" in feed_urls
    assert "https://www.theguardian.com/world/rss" in feed_urls
    assert "https://example-news.test/feed.xml" in feed_urls
    # title preferred over text when present
    bbc = next(i for i in items if i["feed_url"].endswith("bbci.co.uk/news/rss.xml"))
    assert bbc["title"] == "BBC News"


def test_import_opml_ignores_non_feed_outlines() -> None:
    opml = """<opml version="2.0"><body>
      <outline text="just a folder"/>
      <outline text="comment outline" type="link" url="https://x.test"/>
    </body></opml>"""
    assert import_opml(opml) == []


def test_import_opml_bad_xml_returns_empty() -> None:
    assert import_opml("<<not xml>>") == []


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
