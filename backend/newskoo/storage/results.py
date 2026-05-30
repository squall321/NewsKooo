"""Persist :class:`AnalyzeResult` payloads + apply kind-specific side effects.

Every result is recorded as an :class:`Analysis` row (the audit trail of what
the LLM/embedding stage produced, with provider/model/tokens/cost). On top of
that, structured kinds are projected into first-class catalog + link tables so
the data is queryable without re-parsing JSON:

* ``EMBEDDING`` → set ``articles.embedding`` and (re)cluster via
  :func:`newskoo.cluster.events.assign_event`.
* ``ENTITIES``  → upsert :class:`Entity` (by name+type) + :class:`ArticleEntity`.
* ``KEYWORDS``  → upsert :class:`Keyword` (by term) + :class:`ArticleKeyword`.
* ``TOPICS``    → upsert :class:`Topic` (by slug) + :class:`ArticleTopic`.
* ``SUMMARY`` / ``SENTIMENT`` / ``TRANSLATION`` → stored as the Analysis row only.

When a result targets an article, ``articles.status`` is advanced to
``'analyzed'``. Upserts are idempotent so at-least-once redelivery from Kafka is
safe (no duplicate catalog rows, link rows refreshed in place).

Assumed ``result`` shapes (the analyze stage owns these; we read defensively):
  entities:  {"entities": [{"name","type","salience","count","sentiment"}, ...]}
  keywords:  {"keywords": [{"term","weight"}, ...]}  (or bare strings)
  topics:    {"topics":   [{"slug","label","confidence","parent_slug"}, ...]}
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from newskoo.cluster.events import assign_event
from newskoo.core.contracts import AnalysisKind, AnalyzeResult
from newskoo.core.logging import get_logger
from newskoo.models.analysis import Analysis
from newskoo.models.article import Article
from newskoo.models.taxonomy import (
    ArticleEntity,
    ArticleKeyword,
    ArticleTopic,
    Keyword,
    Topic,
)
from newskoo.resolve import resolve_entity

log = get_logger(__name__)


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _slugify(value: str) -> str:
    """Lowercase, hyphenate; a stable fallback slug for topics lacking one."""
    return "-".join(value.strip().lower().split())


async def persist_analysis(session: AsyncSession, res: AnalyzeResult) -> None:
    """Write the :class:`Analysis` row and apply ``res.kind`` side effects.

    Flushes but does not commit (the worker's ``session_scope`` commits).
    """
    session.add(
        Analysis(
            target_type=res.target_type,
            target_id=res.target_id,
            kind=str(res.kind),
            provider=res.provider,
            model=res.model,
            result=res.result or {},
            tokens=res.tokens,
            cost_usd=res.cost_usd,
        )
    )
    await session.flush()

    if res.kind == AnalysisKind.EMBEDDING:
        await _apply_embedding(session, res)
    elif res.kind == AnalysisKind.ENTITIES:
        await _apply_entities(session, res)
    elif res.kind == AnalysisKind.KEYWORDS:
        await _apply_keywords(session, res)
    elif res.kind == AnalysisKind.TOPICS:
        await _apply_topics(session, res)
    # SUMMARY / SENTIMENT / TRANSLATION: Analysis row is the whole side effect.

    # Advance article status once any analysis lands on it.
    if res.target_type == "article":
        article = await session.get(Article, res.target_id)
        if article is not None:
            article.status = "analyzed"
            await session.flush()

    log.info(
        "results.persisted",
        target_type=res.target_type,
        target_id=res.target_id,
        kind=str(res.kind),
        provider=res.provider,
    )


async def _apply_embedding(session: AsyncSession, res: AnalyzeResult) -> None:
    """Store the article embedding and (re)assign it to an event cluster."""
    if res.target_type != "article":
        log.warning("results.embedding_non_article", target_type=res.target_type)
        return
    embedding = res.embedding or res.result.get("embedding")
    if not embedding:
        log.warning("results.embedding_missing", target_id=res.target_id)
        return
    vector = [float(x) for x in embedding]

    article = await session.get(Article, res.target_id)
    if article is None:
        log.warning("results.embedding_unknown_article", target_id=res.target_id)
        return
    article.embedding = vector
    await session.flush()

    await assign_event(session, res.target_id, vector)


async def _apply_entities(session: AsyncSession, res: AnalyzeResult) -> None:
    """Resolve entities (fuzzy/multilingual) and link them to the article.

    Entity identity is delegated to :func:`newskoo.resolve.resolve_entity`,
    which canonicalises names, merges surface variants into ``aliases``, and
    unifies cross-language mentions via embeddings — superseding the old
    exact ``(name, type)`` upsert.
    """
    if res.target_type != "article":
        return
    items = res.result.get("entities", [])
    for item in items:
        if isinstance(item, str):
            item = {"name": item, "type": "unknown"}
        name = (item.get("name") or "").strip()
        if not name:
            continue
        type_ = (item.get("type") or "unknown").strip() or "unknown"
        raw_aliases = item.get("aliases")
        aliases = raw_aliases if isinstance(raw_aliases, list) else None
        entity_id, _ = await resolve_entity(session, name, type_, aliases=aliases)

        link = await session.get(ArticleEntity, (res.target_id, entity_id))
        salience = _as_float(item.get("salience"))
        count = _as_int(item.get("count", 1), default=1)
        sentiment = item.get("sentiment")
        sentiment_f = _as_float(sentiment) if sentiment is not None else None
        if link is None:
            session.add(
                ArticleEntity(
                    article_id=res.target_id,
                    entity_id=entity_id,
                    salience=salience,
                    count=count,
                    sentiment=sentiment_f,
                )
            )
        else:
            link.salience = salience
            link.count = count
            link.sentiment = sentiment_f
    await session.flush()


async def _upsert_keyword(session: AsyncSession, term: str) -> Keyword:
    res = await session.execute(select(Keyword).where(Keyword.term == term))
    keyword = res.scalar_one_or_none()
    if keyword is None:
        keyword = Keyword(term=term)
        session.add(keyword)
        await session.flush()
    return keyword


async def _apply_keywords(session: AsyncSession, res: AnalyzeResult) -> None:
    """Upsert keywords and their per-article weights."""
    if res.target_type != "article":
        return
    items = res.result.get("keywords", [])
    for item in items:
        if isinstance(item, str):
            item = {"term": item, "weight": 0.0}
        term = (item.get("term") or "").strip()
        if not term:
            continue
        keyword = await _upsert_keyword(session, term)
        weight = _as_float(item.get("weight"))

        link = await session.get(ArticleKeyword, (res.target_id, keyword.id))
        if link is None:
            session.add(
                ArticleKeyword(
                    article_id=res.target_id, keyword_id=keyword.id, weight=weight
                )
            )
        else:
            link.weight = weight
    await session.flush()


async def _upsert_topic(session: AsyncSession, slug: str, label: str) -> Topic:
    res = await session.execute(select(Topic).where(Topic.slug == slug))
    topic = res.scalar_one_or_none()
    if topic is None:
        topic = Topic(slug=slug, label=label or slug)
        session.add(topic)
        await session.flush()
    return topic


async def _apply_topics(session: AsyncSession, res: AnalyzeResult) -> None:
    """Upsert topics (by slug) and their per-article confidence links."""
    if res.target_type != "article":
        return
    items = res.result.get("topics", [])
    for item in items:
        if isinstance(item, str):
            item = {"slug": _slugify(item), "label": item}
        label = (item.get("label") or "").strip()
        slug = (item.get("slug") or _slugify(label)).strip()
        if not slug:
            continue
        topic = await _upsert_topic(session, slug, label)
        confidence = _as_float(item.get("confidence"))

        link = await session.get(ArticleTopic, (res.target_id, topic.id))
        if link is None:
            session.add(
                ArticleTopic(
                    article_id=res.target_id,
                    topic_id=topic.id,
                    confidence=confidence,
                )
            )
        else:
            link.confidence = confidence
    await session.flush()
