"""Feed-discovery utilities: RSS autodiscovery, sitemap parsing, OPML import.

All network access goes through a single short-lived ``httpx.AsyncClient`` (or a
caller-supplied one, which tests inject so ``respx`` can mock it). HTML parsing
uses ``selectolax``; XML (sitemaps, OPML) uses the stdlib ``ElementTree`` since
the documents are small and well-formed.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import AsyncIterator, Iterable
from contextlib import asynccontextmanager
from urllib.parse import urljoin, urlparse

import httpx
from selectolax.parser import HTMLParser

from newskoo.core.config import get_settings
from newskoo.core.logging import get_logger

log = get_logger(__name__)

# RSS/Atom MIME types announced in <link rel="alternate">.
_FEED_MIME_TYPES = {
    "application/rss+xml",
    "application/atom+xml",
    "application/feed+json",
    "application/json",
    "text/xml",
    "application/xml",
}

# Conventional feed paths probed when a homepage advertises none.
_COMMON_FEED_PATHS = (
    "/feed",
    "/feed/",
    "/rss",
    "/rss.xml",
    "/feed.xml",
    "/atom.xml",
    "/index.xml",
    "/feeds/posts/default",
    "/rss/index.xml",
)

def _user_agent() -> str:
    agents = get_settings().crawler_user_agents
    return agents[0] if agents else "NewsKooBot/0.1"


@asynccontextmanager
async def _client(
    client: httpx.AsyncClient | None = None,
) -> AsyncIterator[httpx.AsyncClient]:
    """Yield a client: the caller's if given, else a temporary one."""
    if client is not None:
        yield client
        return
    timeout = get_settings().crawler_request_timeout_s
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": _user_agent()},
    ) as owned:
        yield owned


def _normalize(base: str, href: str) -> str:
    return urljoin(base, href.strip())


def _looks_like_feed_path(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(s) or path.rstrip("/").endswith(s.rstrip("/")) for s in _COMMON_FEED_PATHS)


def extract_feed_links(html: str, base_url: str) -> list[dict[str, str]]:
    """Parse ``<link rel="alternate" type="...rss/atom...">`` tags from HTML.

    Returns candidate dicts ``{url, title, type, source}`` (deduped by url).
    """
    tree = HTMLParser(html)
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for node in tree.css("link[rel]"):
        rel = (node.attributes.get("rel") or "").lower()
        if "alternate" not in rel:
            continue
        mime = (node.attributes.get("type") or "").lower().strip()
        href = node.attributes.get("href")
        if not href or mime not in _FEED_MIME_TYPES:
            continue
        url = _normalize(base_url, href)
        if url in seen:
            continue
        seen.add(url)
        out.append(
            {
                "url": url,
                "title": (node.attributes.get("title") or "").strip(),
                "type": mime,
                "source": "link-alternate",
            }
        )
    # Also pick up obvious <a href> links pointing at feed-like paths.
    for node in tree.css("a[href]"):
        href = node.attributes.get("href")
        if not href:
            continue
        url = _normalize(base_url, href)
        if url in seen or not _looks_like_feed_path(url):
            continue
        seen.add(url)
        out.append(
            {"url": url, "title": (node.text() or "").strip(), "type": "", "source": "anchor"}
        )
    return out


async def discover_feeds(
    homepage_url: str,
    *,
    client: httpx.AsyncClient | None = None,
    probe_common_paths: bool = True,
) -> list[dict[str, str]]:
    """Discover candidate feed URLs for a homepage.

    Strategy:
      1. Fetch the homepage and parse ``<link rel="alternate">`` feed tags.
      2. If none found (and ``probe_common_paths``), HEAD/GET common feed paths
         (``/feed``, ``/rss``, ``/index.xml`` …) and keep any that respond OK
         with a feed-ish content type.

    Returns a list of candidate dicts ``{url, title, type, source}``.
    """
    candidates: list[dict[str, str]] = []
    async with _client(client) as cli:
        try:
            resp = await cli.get(homepage_url)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            log.warning("discover.homepage_failed", url=homepage_url, error=str(exc))
            resp = None

        if resp is not None and resp.text:
            candidates.extend(extract_feed_links(resp.text, str(resp.url)))

        if candidates or not probe_common_paths:
            return candidates

        seen = {c["url"] for c in candidates}
        for path in _COMMON_FEED_PATHS:
            probe = _normalize(homepage_url, path)
            if probe in seen:
                continue
            try:
                pr = await cli.get(probe)
            except httpx.HTTPError:
                continue
            if pr.status_code != 200:
                continue
            ctype = pr.headers.get("content-type", "").split(";")[0].lower().strip()
            body_head = pr.text[:512].lstrip().lower()
            if ctype in _FEED_MIME_TYPES or body_head.startswith(("<?xml", "<rss", "<feed")):
                seen.add(probe)
                candidates.append(
                    {"url": probe, "title": "", "type": ctype, "source": "common-path"}
                )
    return candidates


def _strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_sitemap_xml(xml_text: str, base_url: str = "") -> dict[str, list[str]]:
    """Parse sitemap XML, returning ``{"urls": [...], "sitemaps": [...]}``.

    Handles both a ``<urlset>`` (article URLs) and a ``<sitemapindex>`` (nested
    sitemaps). Namespace-agnostic so non-standard feeds still parse.
    """
    urls: list[str] = []
    sitemaps: list[str] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        log.warning("sitemap.parse_failed", base=base_url, error=str(exc))
        return {"urls": urls, "sitemaps": sitemaps}

    root_tag = _strip_ns(root.tag)
    for elem in root.iter():
        if _strip_ns(elem.tag) != "loc" or not elem.text:
            continue
        loc = elem.text.strip()
        if base_url:
            loc = urljoin(base_url, loc)
        if root_tag == "sitemapindex":
            sitemaps.append(loc)
        else:
            urls.append(loc)
    return {"urls": urls, "sitemaps": sitemaps}


async def parse_sitemap(
    url: str,
    *,
    client: httpx.AsyncClient | None = None,
    follow_index: bool = True,
    max_child_sitemaps: int = 10,
) -> list[str]:
    """Fetch a sitemap and return article URLs.

    If ``url`` is a sitemap index and ``follow_index`` is set, fetches up to
    ``max_child_sitemaps`` child sitemaps and aggregates their URLs.
    """
    collected: list[str] = []
    seen: set[str] = set()
    async with _client(client) as cli:
        try:
            resp = await cli.get(url)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            log.warning("sitemap.fetch_failed", url=url, error=str(exc))
            return collected

        parsed = parse_sitemap_xml(resp.text, str(resp.url))
        for u in parsed["urls"]:
            if u not in seen:
                seen.add(u)
                collected.append(u)

        if follow_index and parsed["sitemaps"]:
            for child in parsed["sitemaps"][:max_child_sitemaps]:
                try:
                    cr = await cli.get(child)
                    cr.raise_for_status()
                except httpx.HTTPError:
                    continue
                child_parsed = parse_sitemap_xml(cr.text, str(cr.url))
                for u in child_parsed["urls"]:
                    if u not in seen:
                        seen.add(u)
                        collected.append(u)
    return collected


def import_opml(opml_text: str) -> list[dict[str, str]]:
    """Parse an OPML document into ``[{title, feed_url}, ...]``.

    Reads ``<outline>`` elements with an ``xmlUrl`` attribute (RSS feed URL),
    using ``title`` or ``text`` for the display name. Nested outlines (folders)
    are walked recursively.
    """
    out: list[dict[str, str]] = []
    try:
        root = ET.fromstring(opml_text)
    except ET.ParseError as exc:
        log.warning("opml.parse_failed", error=str(exc))
        return out

    def _walk(elements: Iterable[ET.Element]) -> None:
        for el in elements:
            if _strip_ns(el.tag) == "outline":
                xml_url = el.attrib.get("xmlUrl") or el.attrib.get("xmlurl")
                if xml_url:
                    title = el.attrib.get("title") or el.attrib.get("text") or ""
                    out.append({"title": title.strip(), "feed_url": xml_url.strip()})
            _walk(list(el))

    _walk(list(root))
    return out
