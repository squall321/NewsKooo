"""Real-data harvest demo — runs the actual parse pipeline on live feeds.

Proves end-to-end *collection* without needing Postgres/Kafka/Redis: it fetches
real RSS feeds from the seeded catalog, follows each entry to the article page,
and runs the production extraction (``parse.extract`` → ``parse.language`` →
``parse.transform``) to produce structured :class:`ParsedArticle` records, which
it writes as JSONL. This is the same code path the ``parser`` worker uses; only
Kafka transport and DB persistence are omitted.

    uv run python -m newskoo.harvest --limit-sources 40 --per-feed 5 \
        --out data/harvest_sample.jsonl

Network required; no DB. Politeness is light (a shared concurrency cap) since
this is a bounded one-shot sample, not the continuous crawler.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import feedparser
import httpx

from newskoo.core.contracts import FetchMethod, ParsedArticle, RawDocument
from newskoo.core.logging import configure_logging, get_logger
from newskoo.ingest.html import PlaywrightCrawler
from newskoo.parse.extract import extract_article
from newskoo.parse.language import detect_language
from newskoo.parse.transform import to_parsed_article
from newskoo.sources.seeds import SEED_SOURCES

log = get_logger(__name__)

_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class _RenderBudget:
    """Bounded, concurrency-safe budget for Playwright renders + a recovery tally."""

    def __init__(self, limit: int) -> None:
        self.remaining = limit
        self.recovered = 0
        self._lock = asyncio.Lock()

    async def take(self) -> bool:
        async with self._lock:
            if self.remaining <= 0:
                return False
            self.remaining -= 1
            return True

    async def mark_recovered(self) -> None:
        async with self._lock:
            self.recovered += 1


async def _harvest_source(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    source: dict,
    per_feed: int,
    *,
    render: bool = False,
    crawler: PlaywrightCrawler | None = None,
    render_sem: asyncio.Semaphore | None = None,
    budget: _RenderBudget | None = None,
) -> list[ParsedArticle]:
    feed_url = source.get("feed_url")
    if not feed_url:
        return []
    try:
        async with sem:
            resp = await client.get(feed_url, headers={"User-Agent": _BROWSER_UA})
        feed = feedparser.parse(resp.content)
    except Exception as exc:  # report, never crash the sweep
        log.warning("harvest.feed_failed", source=source.get("name"), error=str(exc))
        return []

    out: list[ParsedArticle] = []
    for entry in feed.entries[:per_feed]:
        link = entry.get("link")
        if not link:
            continue
        # Fetch the real article page; fall back to the feed entry's HTML.
        raw_html = entry.get("summary") or entry.get("title") or ""
        try:
            async with sem:
                page = await client.get(link, headers={"User-Agent": _BROWSER_UA})
            if page.status_code < 400 and page.text:
                raw_html = page.text
        except Exception:  # keep the feed-summary fallback
            pass

        doc = RawDocument(
            source_id=0,
            url=link,
            canonical_url=link,
            fetch_method=FetchMethod.RSS,
            raw_html=raw_html,
            title_hint=entry.get("title"),
            fetched_at=datetime.now(UTC),
        )
        try:
            extracted = extract_article(raw_html, link)
        except Exception as exc:
            log.warning("harvest.parse_failed", url=link, error=str(exc))
            extracted = None

        # Render fallback: JS-shell / soft-paywall pages yield no body via httpx;
        # re-render with Playwright (headless Chromium) and re-extract.
        empty = extracted is None or not (extracted.body or "").strip()
        if empty and render and crawler is not None and budget is not None and await budget.take():
            async with (render_sem or asyncio.Semaphore(1)):
                rendered = await crawler.render(link)
            if rendered:
                try:
                    re_extracted = extract_article(rendered, link)
                except Exception:
                    re_extracted = None
                if re_extracted is not None and (re_extracted.body or "").strip():
                    extracted = re_extracted
                    await budget.mark_recovered()

        if extracted is None or not (extracted.body or "").strip():
            continue
        if not extracted.title:
            extracted.title = entry.get("title", "")
        language = detect_language(extracted.body or extracted.title or "") or None
        try:
            article = to_parsed_article(doc, extracted, language)
        except Exception as exc:
            log.warning("harvest.transform_failed", url=link, error=str(exc))
            continue
        out.append(article)
    return out


async def _run(
    limit_sources: int,
    per_feed: int,
    concurrency: int,
    out: Path,
    *,
    render: bool = False,
    render_limit: int = 10,
    render_concurrency: int = 2,
) -> dict:
    rss = [s for s in SEED_SOURCES if s.get("fetch_method") == "rss" and s.get("feed_url")]
    chosen = rss[:limit_sources] if limit_sources else rss
    sem = asyncio.Semaphore(concurrency)
    timeout = httpx.Timeout(20.0)
    crawler = PlaywrightCrawler() if render else None
    render_sem = asyncio.Semaphore(render_concurrency)
    budget = _RenderBudget(render_limit)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        batches = await asyncio.gather(
            *(
                _harvest_source(
                    client, sem, s, per_feed,
                    render=render, crawler=crawler, render_sem=render_sem, budget=budget,
                )
                for s in chosen
            )
        )

    out.parent.mkdir(parents=True, exist_ok=True)
    langs: Counter[str] = Counter()
    total_words = 0
    samples: list[str] = []
    n = 0
    with out.open("w", encoding="utf-8") as fh:
        for source, articles in zip(chosen, batches, strict=True):
            for art in articles:
                rec = {
                    "source": source["name"],
                    "region": source.get("region"),
                    "url": art.canonical_url,
                    "title": art.title,
                    "language": art.language,
                    "published_at": art.published_at.isoformat() if art.published_at else None,
                    "word_count": art.word_count,
                    "body": art.body,
                }
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                langs[art.language or "?"] += 1
                total_words += art.word_count
                n += 1
                if len(samples) < 12:
                    samples.append(f"[{source['region']}/{art.language}] {art.title[:90]}")

    return {
        "sources_tried": len(chosen),
        "articles": n,
        "rendered_recovered": budget.recovered,
        "languages": dict(langs.most_common()),
        "avg_words": (total_words // n) if n else 0,
        "out": str(out),
        "samples": samples,
    }


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="NewsKoo real-data harvest demo")
    parser.add_argument("--limit-sources", type=int, default=40, help="0 = all rss sources")
    parser.add_argument("--per-feed", type=int, default=5)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--out", default="data/harvest_sample.jsonl")
    parser.add_argument("--render", action="store_true", help="render JS/paywall shells via Playwright")
    parser.add_argument("--render-limit", type=int, default=10, help="max Playwright renders")
    parser.add_argument("--render-concurrency", type=int, default=2)
    args = parser.parse_args()

    summary = asyncio.run(
        _run(
            args.limit_sources, args.per_feed, args.concurrency, Path(args.out),
            render=args.render,
            render_limit=args.render_limit,
            render_concurrency=args.render_concurrency,
        )
    )
    print("\n================ NewsKoo harvest ================")
    print(f"sources tried : {summary['sources_tried']}")
    print(f"articles       : {summary['articles']}")
    print(f"rendered (JS)  : {summary['rendered_recovered']} recovered via Playwright")
    print(f"avg words/body : {summary['avg_words']}")
    print(f"languages      : {summary['languages']}")
    print(f"written to     : {summary['out']}")
    print("\n--- sample headlines (real, just now) ---")
    for s in summary["samples"]:
        print(f"  {s}")


if __name__ == "__main__":
    main()
