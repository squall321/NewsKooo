"""Boilerplate-free article extraction.

Primary path uses :mod:`trafilatura` (text + metadata: title, authors, date,
canonical/url). When trafilatura yields no usable body, a lightweight
:mod:`selectolax` fallback strips obvious chrome (``nav``/``header``/``footer``/
``script``/``style``/``aside``) and pulls the main text + ``<title>`` and
``<meta>`` hints. Text only — no images are retained.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from dateutil import parser as _dtp
from selectolax.parser import HTMLParser

from newskoo.core.logging import get_logger

log = get_logger(__name__)

# Elements that never contain article body text — dropped in the fallback.
_BOILERPLATE_TAGS = (
    "script",
    "style",
    "noscript",
    "template",
    "nav",
    "header",
    "footer",
    "aside",
    "form",
    "figure",
    "figcaption",
    "iframe",
    "svg",
    "button",
)

# Tags that most often wrap the real article body, most-specific first.
_BODY_CANDIDATE_SELECTORS = (
    "article",
    "main",
    "[role=main]",
    "div.article-body",
    "div.article__body",
    "div.post-content",
    "div.entry-content",
    "section",
)


@dataclass(slots=True)
class ExtractedArticle:
    """Result of article extraction. All fields are best-effort.

    ``title``/``body`` are the only strongly-desired fields; everything else is
    metadata that may be absent depending on the page and extractor.
    """

    title: str | None = None
    body: str = ""
    authors: list[str] = field(default_factory=list)
    published_at: datetime | None = None
    canonical_url: str | None = None

    @property
    def has_body(self) -> bool:
        return bool(self.body.strip())


def _coerce_dt(value: object) -> datetime | None:
    """Best-effort parse of a date string/``datetime`` into an aware UTC value."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            dt = _dtp.parse(text)
        except (ValueError, OverflowError, TypeError):
            return None
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    return None


def _authors_from(value: object) -> list[str]:
    """Normalize trafilatura's ``author`` (str/``"a; b"``/list) into a list."""
    out: list[str] = []
    if value is None:
        return out
    raw: list[str]
    if isinstance(value, str):
        raw = value.replace("|", ";").replace(",", ";").split(";")
    elif isinstance(value, (list, tuple)):
        raw = [str(v) for v in value]
    else:
        raw = [str(value)]
    for name in raw:
        cleaned = name.strip()
        if cleaned and cleaned not in out:
            out.append(cleaned)
    return out


def _meta_value(meta: object, *keys: str) -> object:
    """Read ``keys`` from a trafilatura result that may be a dict or object."""
    for key in keys:
        if isinstance(meta, dict):
            if meta.get(key) not in (None, ""):
                return meta[key]
        else:
            val = getattr(meta, key, None)
            if val not in (None, ""):
                return val
    return None


def _extract_trafilatura(raw_html: str, url: str) -> ExtractedArticle | None:
    """Run trafilatura's ``bare_extraction``; return ``None`` on no body/error."""
    try:
        import trafilatura
    except ImportError:  # pragma: no cover - dependency is declared
        return None

    try:
        result = trafilatura.bare_extraction(
            raw_html,
            url=url or None,
            with_metadata=True,
            include_comments=False,
            include_tables=True,
            include_images=False,
            include_links=False,
            favor_precision=True,
        )
    except Exception as exc:  # third-party parser must never be fatal
        log.warning("extract.trafilatura_error", url=url, error=str(exc))
        return None

    if not result:
        return None

    body = _meta_value(result, "text", "raw_text")
    body_text = str(body).strip() if body else ""
    if not body_text:
        return None

    title = _meta_value(result, "title")
    canonical = _meta_value(result, "canonical_url", "canonical", "url", "source")
    date = _meta_value(result, "date")

    return ExtractedArticle(
        title=str(title).strip() if title else None,
        body=body_text,
        authors=_authors_from(_meta_value(result, "author", "authors")),
        published_at=_coerce_dt(date),
        canonical_url=str(canonical).strip() if canonical else None,
    )


def _meta_content(tree: HTMLParser, *selectors: str) -> str | None:
    for selector in selectors:
        node = tree.css_first(selector)
        if node is not None:
            content = (node.attributes.get("content") or "").strip()
            if content:
                return content
    return None


def _extract_selectolax(raw_html: str, url: str) -> ExtractedArticle:
    """Lightweight fallback: strip chrome, take the densest text container."""
    tree = HTMLParser(raw_html)

    for tag in _BOILERPLATE_TAGS:
        for node in tree.css(tag):
            node.decompose()

    # Title: <meta og:title> → <title> → first <h1>.
    title = _meta_content(tree, 'meta[property="og:title"]', 'meta[name="twitter:title"]')
    if not title:
        title_node = tree.css_first("title")
        if title_node is not None:
            title = title_node.text(strip=True) or None
    if not title:
        h1 = tree.css_first("h1")
        if h1 is not None:
            title = h1.text(strip=True) or None

    # Body: pick the candidate container with the most text, else <body>.
    best_text = ""
    for selector in _BODY_CANDIDATE_SELECTORS:
        for node in tree.css(selector):
            text = node.text(separator="\n", strip=True)
            if len(text) > len(best_text):
                best_text = text
    if not best_text.strip():
        body_node = tree.css_first("body")
        if body_node is not None:
            best_text = body_node.text(separator="\n", strip=True)

    # Collapse blank lines.
    lines = [ln.strip() for ln in best_text.splitlines()]
    body = "\n".join(ln for ln in lines if ln)

    canonical = None
    link = tree.css_first('link[rel="canonical"]')
    if link is not None:
        canonical = (link.attributes.get("href") or "").strip() or None
    if not canonical:
        canonical = _meta_content(tree, 'meta[property="og:url"]')

    date_str = _meta_content(
        tree,
        'meta[property="article:published_time"]',
        'meta[name="article:published_time"]',
        'meta[itemprop="datePublished"]',
        'meta[name="date"]',
        'meta[name="pubdate"]',
    )
    author_str = _meta_content(
        tree,
        'meta[name="author"]',
        'meta[property="article:author"]',
    )

    return ExtractedArticle(
        title=title,
        body=body,
        authors=_authors_from(author_str),
        published_at=_coerce_dt(date_str),
        canonical_url=canonical or (url or None),
    )


def extract_article(raw_html: str, url: str) -> ExtractedArticle:
    """Extract a boilerplate-free article from ``raw_html``.

    Tries trafilatura first (best precision + metadata). If it returns no body,
    falls back to a selectolax-based extractor. The returned
    :class:`ExtractedArticle` always has at least an empty ``body`` string.
    """
    if not raw_html or not raw_html.strip():
        return ExtractedArticle(canonical_url=url or None)

    extracted = _extract_trafilatura(raw_html, url)
    if extracted is not None and extracted.has_body:
        if not extracted.canonical_url:
            extracted.canonical_url = url or None
        return extracted

    log.debug("extract.fallback_selectolax", url=url)
    return _extract_selectolax(raw_html, url)
