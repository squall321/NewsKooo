"""Event-clustering tests against a mocked AsyncSession (no pgvector/DB).

Exercises :func:`cluster.events.assign_event`'s attach-vs-seed decision driven
by a mocked nearest-event cosine distance, plus the aggregate recomputation.

The session is scripted: ``execute`` returns the nearest-event row first (or
``None``), then the aggregate tuple from ``_recompute_aggregates``. ``get``
returns the incoming article.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from newskoo.cluster import events
from newskoo.models.article import Article
from newskoo.models.event import Event, EventArticle

_PUB = datetime(2026, 5, 29, tzinfo=UTC)


def _nearest_row(event: Event | None, distance: float):
    """A fake ``execute().first()`` result for ``_nearest_event``."""
    res = MagicMock()
    res.first.return_value = None if event is None else (event, distance)
    return res


def _agg_row(article_count, source_count, language_count, first_pub, last_pub):
    """A fake ``execute().one()`` result for ``_recompute_aggregates``."""
    res = MagicMock()
    res.one.return_value = (
        article_count,
        source_count,
        language_count,
        first_pub,
        last_pub,
    )
    return res


def _session(article: Article, execute_results: list[MagicMock]) -> AsyncMock:
    session = AsyncMock()
    added: list[object] = []
    seq = {"n": 1000}

    def _add(obj: object) -> None:
        added.append(obj)

    async def _flush() -> None:
        for obj in added:
            if isinstance(obj, Event) and getattr(obj, "id", None) is None:
                seq["n"] += 1
                obj.id = seq["n"]

    session.execute = AsyncMock(side_effect=list(execute_results))
    session.get = AsyncMock(return_value=article)
    session.add = MagicMock(side_effect=_add)
    session.flush = AsyncMock(side_effect=_flush)
    session.added = added  # type: ignore[attr-defined]
    return session


async def test_attach_to_existing_event_above_threshold() -> None:
    # cosine distance 0.10 → similarity 0.90 >= 0.82 → attach.
    article = Article(id=7, source_id=3, language="en", title="t", published_at=_PUB)
    existing = Event(id=500, title="seed", centroid=[1.0, 0.0, 0.0], article_count=1)
    session = _session(
        article,
        [
            _nearest_row(existing, 0.10),
            _agg_row(2, 2, 1, _PUB, _PUB),  # after attach: 2 articles, 2 sources
        ],
    )

    event_id = await events.assign_event(session, 7, [0.9, 0.1, 0.0])

    assert event_id == 500
    assert article.event_id == 500
    links = [o for o in session.added if isinstance(o, EventArticle)]
    assert len(links) == 1
    assert links[0].is_seed is False
    assert links[0].event_id == 500
    assert round(links[0].similarity, 4) == 0.9
    # Centroid moved via running mean of 1 existing vector + new embedding.
    assert existing.centroid == [(1.0 * 1 + 0.9) / 2, (0.0 + 0.1) / 2, 0.0]
    # Aggregates recomputed from membership.
    assert existing.article_count == 2
    assert existing.source_count == 2
    assert existing.language_count == 1
    # No new Event created.
    assert not [o for o in session.added if isinstance(o, Event)]


async def test_create_new_event_below_threshold() -> None:
    # cosine distance 0.50 → similarity 0.50 < 0.82 → seed a new event.
    article = Article(id=8, source_id=4, language="ko", title="새 사건", published_at=_PUB)
    existing = Event(id=600, title="other", centroid=[0.0, 1.0], article_count=5)
    session = _session(
        article,
        [
            _nearest_row(existing, 0.50),
            _agg_row(1, 1, 1, _PUB, _PUB),  # the brand-new single-article event
        ],
    )

    vec = [1.0, 0.0]
    event_id = await events.assign_event(session, 8, vec)

    new_events = [o for o in session.added if isinstance(o, Event)]
    assert len(new_events) == 1
    seed = new_events[0]
    assert event_id == seed.id
    assert article.event_id == seed.id
    assert seed.centroid == vec  # centroid seeded to the article embedding
    assert seed.title == "새 사건"
    links = [o for o in session.added if isinstance(o, EventArticle)]
    assert len(links) == 1
    assert links[0].is_seed is True
    assert links[0].similarity == 1.0
    assert seed.article_count == 1
    # Existing event untouched.
    assert existing.article_count == 5


async def test_create_new_event_when_no_events_exist() -> None:
    article = Article(id=9, source_id=5, language="en", title="first ever", published_at=_PUB)
    session = _session(
        article,
        [
            _nearest_row(None, 0.0),  # no events at all
            _agg_row(1, 1, 1, _PUB, _PUB),
        ],
    )

    vec = [0.5, 0.5]
    event_id = await events.assign_event(session, 9, vec)

    new_events = [o for o in session.added if isinstance(o, Event)]
    assert len(new_events) == 1
    assert event_id == new_events[0].id
    assert new_events[0].centroid == vec
    seed_links = [o for o in session.added if isinstance(o, EventArticle)]
    assert len(seed_links) == 1 and seed_links[0].is_seed is True


async def test_exact_threshold_boundary_attaches() -> None:
    # similarity exactly 0.82 (distance 0.18) → attach (>= is inclusive).
    article = Article(id=10, source_id=6, language="en", title="t", published_at=_PUB)
    existing = Event(id=700, title="seed", centroid=[1.0], article_count=1)
    session = _session(
        article,
        [
            _nearest_row(existing, 0.18),
            _agg_row(2, 1, 1, _PUB, _PUB),
        ],
    )

    event_id = await events.assign_event(session, 10, [1.0])
    assert event_id == 700
    assert article.event_id == 700
