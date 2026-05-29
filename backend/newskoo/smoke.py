"""Live smoke test — validates the running stack end-to-end.

Run against live, migrated services (Postgres up + ``alembic upgrade head``):

    uv run python -m newskoo.smoke            # deterministic DB stack check
    uv run python -m newskoo.smoke --live-rss # also fetch+parse a real RSS feed

What it checks:
- **DB roundtrip**: upsert a source, persist a :class:`ParsedArticle`, read it back.
- **Full-text search**: the generated ``tsv`` column matches a query term.
- **pgvector**: set an embedding and run a cosine nearest-neighbour query
  (exercises the HNSW index).
- **(--live-rss)**: fetch a real feed over the network, extract + transform +
  persist one article (best-effort; requires outbound network).

Exits non-zero on failure so CI / the live-integration script can gate on it.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime

import httpx
from sqlalchemy import func, select

from newskoo.core import accel
from newskoo.core.config import get_settings
from newskoo.core.contracts import FetchMethod, ParsedArticle, RawDocument
from newskoo.core.db import dispose_engine, session_scope
from newskoo.core.logging import configure_logging, get_logger
from newskoo.models.article import Article
from newskoo.parse.extract import extract_article
from newskoo.parse.language import detect_language
from newskoo.parse.transform import to_parsed_article
from newskoo.sources.registry import upsert_source
from newskoo.sources.schemas import SourceCreate
from newskoo.storage.persist import persist_parsed

log = get_logger(__name__)

_SMOKE_URL = "https://smoke.newskoo.local/articles/markets-rally"
_SMOKE_BODY = (
    "Global markets rallied on Thursday after a string of strong technology "
    "earnings, as investors rotated into semiconductors and artificial-intelligence "
    "infrastructure names. Analysts cited resilient demand and easing supply "
    "constraints. Bond yields slipped while the dollar held steady."
)
_DEFAULT_FEED = "http://feeds.bbci.co.uk/news/world/rss.xml"


async def _db_roundtrip() -> dict:
    settings = get_settings()
    dim = settings.embedding_dim

    async with session_scope() as session:
        source = await upsert_source(
            session,
            SourceCreate(
                name="NewsKoo Smoke Source",
                homepage_url="https://smoke.newskoo.local",
                feed_url="https://smoke.newskoo.local/rss.xml",
                fetch_method=FetchMethod.RSS,
                region="GLOBAL",
                languages=["en"],
                categories=["markets", "technology"],
            ),
        )
        parsed = ParsedArticle(
            source_id=source.id,
            url=_SMOKE_URL,
            canonical_url=_SMOKE_URL,
            title="Global markets rally on tech earnings",
            body=_SMOKE_BODY,
            language="en",
            authors=["Smoke Bot"],
            published_at=datetime.now(UTC),
            fetched_at=datetime.now(UTC),
            content_hash=accel.content_hash(_SMOKE_BODY).hex(),
            simhash=accel.simhash64(_SMOKE_BODY),
            word_count=len(_SMOKE_BODY.split()),
        )
        article_id, is_new = await persist_parsed(session, parsed)

        # Exercise pgvector: write an embedding (unit vector on axis 0).
        vec = [0.0] * dim
        vec[0] = 1.0
        article = await session.get(Article, article_id)
        if article is not None:
            article.embedding = vec

    # Read back in a fresh transaction.
    async with session_scope() as session:
        total = int(await session.scalar(select(func.count()).select_from(Article)) or 0)
        fts = (
            await session.execute(
                select(Article.id, Article.title)
                .where(Article.tsv.op("@@")(func.websearch_to_tsquery("simple", "markets")))
                .limit(5)
            )
        ).all()
        probe = [0.0] * dim
        probe[0] = 1.0
        nearest_id = (
            await session.execute(
                select(Article.id).order_by(Article.embedding.cosine_distance(probe)).limit(1)
            )
        ).scalar_one_or_none()

    return {
        "article_id": article_id,
        "is_new": is_new,
        "total_articles": total,
        "fts_hits": len(fts),
        "vector_nearest_id": nearest_id,
    }


async def _live_rss(feed_url: str) -> dict:
    """Best-effort: fetch a real feed, parse+persist its first entry."""
    import feedparser

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        resp = await client.get(feed_url, headers={"User-Agent": "NewsKooBot/0.1 smoke"})
        resp.raise_for_status()
    feed = feedparser.parse(resp.content)
    if not feed.entries:
        return {"persisted": 0, "note": "feed had no entries"}

    entry = feed.entries[0]
    link = entry.get("link") or feed_url
    raw_html = entry.get("summary") or entry.get("title") or ""
    doc = RawDocument(
        source_id=0,  # smoke uses the seeded smoke source below
        url=link,
        canonical_url=link,
        fetch_method=FetchMethod.RSS,
        raw_html=raw_html,
        title_hint=entry.get("title"),
        fetched_at=datetime.now(UTC),
    )
    extracted = extract_article(raw_html, link)
    if not extracted.title:
        extracted.title = entry.get("title", "(untitled)")
    language = detect_language(extracted.body or extracted.title or "") or "en"

    async with session_scope() as session:
        source = await upsert_source(
            session,
            SourceCreate(
                name="NewsKoo Smoke RSS",
                homepage_url=feed_url,
                feed_url=feed_url,
                fetch_method=FetchMethod.RSS,
                region="GLOBAL",
                languages=[language],
                categories=["general"],
            ),
        )
        doc.source_id = source.id
        parsed = to_parsed_article(doc, extracted, language)
        article_id, is_new = await persist_parsed(session, parsed)

    return {"persisted": 1, "article_id": article_id, "is_new": is_new, "title": extracted.title}


async def _main(live_rss: bool, feed_url: str) -> int:
    log.info("smoke.start", live_rss=live_rss)
    db = await _db_roundtrip()
    log.info("smoke.db_roundtrip", **db)
    ok = db["total_articles"] >= 1 and db["fts_hits"] >= 1 and db["vector_nearest_id"] is not None

    rss = None
    if live_rss:
        try:
            rss = await _live_rss(feed_url)
            log.info("smoke.live_rss", **rss)
        except Exception as exc:
            log.warning("smoke.live_rss_failed", error=str(exc))
            rss = {"persisted": 0, "error": str(exc)}

    await dispose_engine()

    print("── NewsKoo smoke ──")
    print(f"  DB roundtrip : {db}")
    if rss is not None:
        print(f"  live RSS     : {rss}")
    print(f"  RESULT       : {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="NewsKoo live smoke test")
    parser.add_argument("--live-rss", action="store_true", help="also fetch+parse a real feed")
    parser.add_argument("--feed", default=_DEFAULT_FEED, help="RSS feed URL for --live-rss")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_main(args.live_rss, args.feed)))


if __name__ == "__main__":
    main()
