"""Embedding-based clustering of articles into events (pgvector).

One real-world story = one :class:`~newskoo.models.event.Event` spanning many
articles, sources, and languages. When an article's embedding arrives, we find
the nearest existing event by **cosine distance** over ``Event.centroid`` and:

* attach to it when cosine *similarity* ``(1 - distance)`` is at least
  ``settings.cluster_similarity_threshold`` (default 0.82) — inserting an
  :class:`~newskoo.models.event.EventArticle`, stamping ``article.event_id``,
  and updating the event's aggregates (article/source/language counts, time
  bounds) plus a running-mean centroid; or
* seed a **new** event from this article (``is_seed=True``, centroid = the
  article embedding) when nothing is close enough.

Aggregates are recomputed from current membership so they stay correct under
at-least-once delivery (a replayed result must not double-count).
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from newskoo.core.config import get_settings
from newskoo.core.logging import get_logger
from newskoo.models.article import Article
from newskoo.models.event import Event, EventArticle

log = get_logger(__name__)


async def _nearest_event(
    session: AsyncSession, embedding: list[float]
) -> tuple[Event, float] | None:
    """Closest event by cosine distance to ``embedding`` (or ``None``).

    Returns ``(event, distance)`` where ``distance`` is the pgvector cosine
    distance in ``[0, 2]``; cosine similarity is ``1 - distance``. Events with a
    NULL centroid (not yet seeded) are skipped.
    """
    distance = Event.centroid.cosine_distance(embedding)
    stmt = (
        select(Event, distance.label("distance"))
        .where(Event.centroid.is_not(None))
        .order_by(distance)
        .limit(1)
    )
    res = await session.execute(stmt)
    row = res.first()
    if row is None:
        return None
    event, dist = row
    return event, float(dist)


def _running_mean(
    centroid: list[float] | None, count: int, embedding: list[float]
) -> list[float]:
    """Incremental mean of ``count`` existing vectors plus a new ``embedding``.

    With no prior centroid (or a zero count) the new embedding *is* the mean.
    """
    if centroid is None or count <= 0:
        return list(embedding)
    n = float(count)
    return [(c * n + e) / (n + 1.0) for c, e in zip(centroid, embedding, strict=True)]


async def _recompute_aggregates(session: AsyncSession, event: Event) -> None:
    """Refresh count/time aggregates for ``event`` from current membership.

    Counts are derived with DISTINCT over the joined articles so source/language
    diversity is exact and idempotent under replays.
    """
    stmt = select(
        func.count(Article.id),
        func.count(func.distinct(Article.source_id)),
        func.count(func.distinct(Article.language)),
        func.min(Article.published_at),
        func.max(Article.published_at),
    ).where(Article.event_id == event.id)
    res = await session.execute(stmt)
    article_count, source_count, language_count, first_pub, last_pub = res.one()

    event.article_count = int(article_count or 0)
    event.source_count = int(source_count or 0)
    event.language_count = int(language_count or 0)

    now = datetime.now(UTC)
    started = first_pub or event.started_at or now
    last_seen = last_pub or now
    event.started_at = started
    event.last_seen_at = last_seen


async def assign_event(
    session: AsyncSession, article_id: int, embedding: list[float]
) -> int:
    """Attach ``article_id`` to the nearest event or seed a new one.

    Decision: join the nearest event when cosine similarity
    ``(1 - cosine_distance) >= settings.cluster_similarity_threshold``; otherwise
    create a fresh seed event. Returns the resulting ``event_id``.

    Side effects (within the caller's transaction; flushes but never commits):
      * inserts an :class:`EventArticle` membership row with the similarity score,
      * sets ``article.event_id``,
      * updates the event's centroid (running mean on join; the embedding itself
        for a new seed) and recomputes its aggregates from membership.
    """
    settings = get_settings()
    article = await session.get(Article, article_id)
    if article is None:
        raise ValueError(f"assign_event: article {article_id} not found")

    nearest = await _nearest_event(session, embedding)
    similarity = (1.0 - nearest[1]) if nearest is not None else -1.0

    if nearest is not None and similarity >= settings.cluster_similarity_threshold:
        event, _dist = nearest
        # Update centroid before flipping membership so the running mean uses the
        # pre-attach count.
        event.centroid = _running_mean(event.centroid, event.article_count, embedding)
        article.event_id = event.id
        session.add(
            EventArticle(
                event_id=event.id,
                article_id=article_id,
                similarity=similarity,
                is_seed=False,
            )
        )
        await session.flush()
        await _recompute_aggregates(session, event)
        await session.flush()
        log.info(
            "cluster.attached",
            article_id=article_id,
            event_id=event.id,
            similarity=round(similarity, 4),
        )
        return int(event.id)

    # Nothing close enough → seed a new event from this article.
    now = datetime.now(UTC)
    started = article.published_at or now
    event = Event(
        title=article.title or "",
        started_at=started,
        last_seen_at=started,
        centroid=list(embedding),
        article_count=0,
        source_count=0,
        language_count=0,
    )
    session.add(event)
    await session.flush()  # assign event.id

    article.event_id = event.id
    session.add(
        EventArticle(
            event_id=event.id,
            article_id=article_id,
            similarity=1.0,
            is_seed=True,
        )
    )
    await session.flush()
    await _recompute_aggregates(session, event)
    await session.flush()
    log.info("cluster.seeded", article_id=article_id, event_id=event.id)
    return int(event.id)
