"""HTML crawler implementing :class:`SourceConnector` for ``fetch_method=="html"``.

Two operating modes, chosen by what the source describes:

* **Listing / section page** — when ``source.politeness['html']['mode']`` is
  ``"listing"`` (or the homepage looks like an index): fetch the page, extract
  article links with :mod:`selectolax`, then fetch each article (round-robin,
  rate-limited, robots-checked) and yield its ``raw_html``.
* **Single article page** — fetch the configured URL(s) and yield ``raw_html``.

All requests pass through :class:`~newskoo.ingest.politeness.PolitenessEngine`.

For JS-heavy / bot-sensitive sites a :class:`PlaywrightCrawler` is provided
behind a lazy import of the optional ``playwright`` extra; if Playwright is not
installed it logs and falls back to plain :mod:`httpx`.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin, urlsplit

import httpx
from selectolax.parser import HTMLParser

from newskoo.core.logging import get_logger
from newskoo.ingest.politeness import PolitenessEngine, domain_of

if TYPE_CHECKING:
    from newskoo.models.source import Source

log = get_logger(__name__)

# Conservative cap on links followed from a single listing page per cycle.
_DEFAULT_MAX_LINKS = 40


def _html_options(source: Source) -> dict[str, Any]:
    politeness = getattr(source, "politeness", None) or {}
    opts = politeness.get("html")
    return dict(opts) if isinstance(opts, dict) else {}


def _rps_for(source: Source, engine: PolitenessEngine) -> float:
    politeness = getattr(source, "politeness", None) or {}
    rps = politeness.get("rps")
    if isinstance(rps, (int, float)) and rps > 0:
        return float(rps)
    return engine.default_rps or 0.5


def extract_article_links(
    html: str, base_url: str, *, selector: str | None = None, same_host: bool = True
) -> list[str]:
    """Extract candidate article URLs from a listing/section page.

    Uses ``selector`` (CSS) when provided, else all ``<a href>`` anchors.
    Resolves relative URLs against ``base_url``, dedupes (insertion order), drops
    fragments/mailto/javascript, and (by default) keeps only same-host links.
    """
    tree = HTMLParser(html)
    base_host = (urlsplit(base_url).hostname or "").lower()
    nodes = tree.css(selector) if selector else tree.css("a[href]")
    seen: set[str] = set()
    out: list[str] = []
    for node in nodes:
        href = node.attributes.get("href") if node.attributes else None
        if not href:
            continue
        href = href.strip()
        if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
            continue
        url = urljoin(base_url, href).split("#", 1)[0]
        scheme = urlsplit(url).scheme
        if scheme not in ("http", "https"):
            continue
        if same_host and (urlsplit(url).hostname or "").lower() != base_host:
            continue
        if url in seen:
            continue
        seen.add(url)
        out.append(url)
    return out


@dataclass
class HtmlConnector:
    """Collector for ``fetch_method == "html"`` sources (static httpx + selectolax)."""

    fetch_method: str = "html"
    engine: PolitenessEngine = field(default_factory=PolitenessEngine)
    use_playwright: bool = False

    async def _get(
        self, url: str, client: httpx.AsyncClient, rps: float
    ) -> httpx.Response | None:
        """Polite GET: robots-check, rate-limit, fetch; ``None`` on disallow/error."""
        ua = self.engine.user_agents[0] if self.engine.user_agents else None
        if not await self.engine.can_fetch(url, ua, client=client):
            log.info("html.robots_disallow", url=url)
            return None
        await self.engine.acquire(domain_of(url), rps)
        try:
            resp = await client.get(url)
        except httpx.HTTPError as exc:
            log.warning("html.fetch_failed", url=url, error=str(exc))
            return None
        if resp.status_code >= 400:
            log.warning("html.http_error", url=url, status=resp.status_code)
            return None
        return resp

    def _item_from(self, resp: httpx.Response) -> dict[str, Any]:
        ctype = resp.headers.get("content-type", "").split(";")[0].strip() or None
        return {
            "url": str(resp.url),
            "raw_html": resp.text,
            "http_status": resp.status_code,
            "content_type": ctype,
        }

    async def fetch(self, source: Source) -> AsyncIterator[dict]:
        opts = _html_options(source)
        rps = _rps_for(source, self.engine)
        mode = (opts.get("mode") or "").lower()
        start_urls: list[str] = list(opts.get("urls") or [])
        listing_url = opts.get("listing_url") or getattr(source, "homepage_url", None)

        if self.use_playwright or opts.get("playwright"):
            async for item in self._fetch_playwright(source, opts, rps):
                yield item
            return

        async with self.engine.client() as client:
            if mode == "listing" or (not start_urls and opts.get("link_selector")):
                async for item in self._fetch_listing(
                    listing_url, opts, client, rps
                ):
                    yield item
                return

            # Single-article mode: explicit urls, else the homepage itself.
            targets = start_urls or ([listing_url] if listing_url else [])
            urls_by_domain: dict[str, list[str]] = {}
            for u in targets:
                urls_by_domain.setdefault(domain_of(u), []).append(u)
            for url in self.engine.interleave(urls_by_domain):
                resp = await self._get(url, client, rps)
                if resp is not None:
                    yield self._item_from(resp)

    async def _fetch_listing(
        self,
        listing_url: str | None,
        opts: dict[str, Any],
        client: httpx.AsyncClient,
        rps: float,
    ) -> AsyncIterator[dict[str, Any]]:
        if not listing_url:
            log.warning("html.no_listing_url")
            return
        page = await self._get(listing_url, client, rps)
        if page is None:
            return
        links = extract_article_links(
            page.text,
            str(page.url),
            selector=opts.get("link_selector"),
            same_host=bool(opts.get("same_host", True)),
        )
        max_links = int(opts.get("max_links") or _DEFAULT_MAX_LINKS)
        links = links[:max_links]
        urls_by_domain: dict[str, list[str]] = {}
        for u in links:
            urls_by_domain.setdefault(domain_of(u), []).append(u)
        for url in self.engine.interleave(urls_by_domain):
            resp = await self._get(url, client, rps)
            if resp is not None:
                yield self._item_from(resp)

    async def _fetch_playwright(
        self, source: Source, opts: dict[str, Any], rps: float
    ) -> AsyncIterator[dict[str, Any]]:
        crawler = PlaywrightCrawler(self.engine)
        targets: list[str] = list(opts.get("urls") or [])
        if not targets:
            home = getattr(source, "homepage_url", None)
            if home:
                targets = [home]
        for url in targets:
            ua = self.engine.user_agents[0] if self.engine.user_agents else None
            if not await self.engine.can_fetch(url, ua):
                log.info("html.robots_disallow", url=url)
                continue
            await self.engine.acquire(domain_of(url), rps)
            html = await crawler.render(url)
            if html is not None:
                yield {
                    "url": url,
                    "raw_html": html,
                    "http_status": 200,
                    "content_type": "text/html",
                }


@dataclass
class PlaywrightCrawler:
    """Renders JS-heavy pages via Playwright when available, else httpx fallback.

    The ``playwright`` package is an *optional* extra (``newskoo[browser]``); it
    is imported lazily so the ingestion module loads fine without it.
    """

    engine: PolitenessEngine = field(default_factory=PolitenessEngine)
    wait_until: str = "networkidle"

    async def render(self, url: str) -> str | None:
        """Return the rendered HTML of ``url``, or ``None`` on failure."""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            log.info("html.playwright_unavailable_fallback", url=url)
            return await self._httpx_fallback(url)

        ua = self.engine.next_user_agent()
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(
                    headless=True,
                    proxy={"server": self.engine.proxy_url} if self.engine.proxy_url else None,
                )
                try:
                    context = await browser.new_context(user_agent=ua)
                    page = await context.new_page()
                    await page.goto(url, wait_until=self.wait_until)
                    return await page.content()
                finally:
                    await browser.close()
        except Exception as exc:  # browser/runtime errors are diverse
            log.warning("html.playwright_failed", url=url, error=str(exc))
            return await self._httpx_fallback(url)

    async def _httpx_fallback(self, url: str) -> str | None:
        try:
            async with self.engine.client() as client:
                resp = await client.get(url)
        except httpx.HTTPError as exc:
            log.warning("html.fallback_failed", url=url, error=str(exc))
            return None
        if resp.status_code >= 400:
            return None
        return resp.text
