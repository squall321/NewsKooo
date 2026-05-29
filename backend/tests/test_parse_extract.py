"""Extraction tests: trafilatura/selectolax pull the article, drop chrome.

No network — a static HTML news page string is fed to ``extract_article``.
"""

from __future__ import annotations

from newskoo.parse.extract import ExtractedArticle, extract_article

_NEWS_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Markets rally as inflation cools | Example News</title>
  <link rel="canonical" href="https://news.example.com/markets/rally-2026">
  <meta property="og:title" content="Markets rally as inflation cools">
  <meta name="author" content="Jane Doe; John Roe">
  <meta property="article:published_time" content="2026-05-28T14:30:00Z">
</head>
<body>
  <header id="site-header">
    <nav><a href="/">Home</a><a href="/markets">Markets</a><a href="/tech">Tech</a></nav>
  </header>
  <aside class="sidebar">Subscribe to our newsletter! Sign up now for breaking alerts.</aside>
  <main>
    <article>
      <h1>Markets rally as inflation cools</h1>
      <p>Global equity markets advanced sharply on Thursday after fresh data
      showed consumer price growth slowing more than economists had expected,
      reinforcing bets that central banks may pause further rate increases.</p>
      <p>The benchmark index closed up two percent, its strongest single-day
      gain in three months, as technology and consumer shares led the advance.
      Analysts cautioned that a single report does not establish a trend.</p>
      <p>Bond yields fell in tandem, with the ten-year note retreating to its
      lowest level since the start of the quarter as traders repriced the path
      of monetary policy for the remainder of the year.</p>
    </article>
  </main>
  <footer id="site-footer">
    <p>Copyright 2026 Example News. All rights reserved. Terms of Service.</p>
    <nav><a href="/privacy">Privacy</a><a href="/contact">Contact</a></nav>
  </footer>
  <script>console.log("tracking pixel");</script>
</body>
</html>
"""


def test_extract_returns_extracted_article() -> None:
    result = extract_article(_NEWS_HTML, "https://news.example.com/markets/rally-2026")
    assert isinstance(result, ExtractedArticle)
    assert result.has_body


def test_extract_pulls_title_and_body() -> None:
    result = extract_article(_NEWS_HTML, "https://news.example.com/markets/rally-2026")
    assert result.title is not None
    assert "inflation cools" in result.title.lower()
    # Core article sentences are present.
    assert "consumer price growth slowing" in result.body
    assert "strongest single-day" in result.body


def test_extract_strips_boilerplate() -> None:
    result = extract_article(_NEWS_HTML, "https://news.example.com/markets/rally-2026")
    body_lower = result.body.lower()
    # Nav / footer / sidebar / script chrome must not leak into the body.
    assert "all rights reserved" not in body_lower
    assert "subscribe to our newsletter" not in body_lower
    assert "tracking pixel" not in body_lower
    # Footer nav link text ("Privacy"/"Contact") must not leak in.
    assert "privacy" not in body_lower


def test_extract_canonical_url_defaults_to_input_url() -> None:
    url = "https://news.example.com/markets/rally-2026"
    result = extract_article(_NEWS_HTML, url)
    assert result.canonical_url is not None
    assert "rally-2026" in result.canonical_url


def test_extract_empty_html_yields_empty_body() -> None:
    result = extract_article("", "https://news.example.com/x")
    assert isinstance(result, ExtractedArticle)
    assert result.body == ""
    assert result.canonical_url == "https://news.example.com/x"


def test_selectolax_fallback_extracts_when_no_article_semantics() -> None:
    # No <article>/<main>; trafilatura may bail → exercise fallback path too.
    html = """<html><head><title>Fallback Title</title>
    <link rel="canonical" href="https://x.test/a"></head>
    <body><nav>Menu One Two Three</nav>
    <div class="entry-content">
      <p>This is the substantive body paragraph that should survive extraction
      because it is by far the longest text block on the page and contains the
      real reporting that a reader actually cares about reading today.</p>
    </div>
    <footer>Footer junk copyright notice</footer></body></html>"""
    from newskoo.parse.extract import _extract_selectolax

    result = _extract_selectolax(html, "https://x.test/a")
    assert "substantive body paragraph" in result.body
    assert "Footer junk" not in result.body
    assert result.canonical_url == "https://x.test/a"
