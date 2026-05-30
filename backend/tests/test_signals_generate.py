"""generate_signals tests against a mocked AsyncSession (no live DB).

The three query shapes issued by :func:`generate_signals` are routed by
inspecting the compiled SQL text:

1. link query   — securities ⋈ entity_securities → rows ``(security_id, entity_id, confidence)``
2. article query — articles ⋈ article_entities    → rows ``(article_id, published_at,
                    event_id, entity_id, salience, sentiment)``
3. sentiment query — analysis (kind='sentiment')   → ``.scalars().first()`` → Analysis|None

Inserted :class:`Signal` rows are captured via ``add`` and assigned ids on
``flush`` (mirroring autoincrement).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from newskoo.models.analysis import Analysis
from newskoo.models.finance import Signal
from newskoo.signals.generate import generate_signals

_NOW = datetime(2026, 5, 29, 12, 0, 0, tzinfo=UTC)


def _rows_result(rows: list) -> MagicMock:
    res = MagicMock()
    res.all.return_value = rows
    return res


def _scalar_first_result(obj: object) -> MagicMock:
    scalars = MagicMock()
    scalars.first.return_value = obj
    res = MagicMock()
    res.scalars.return_value = scalars
    return res


def _session(
    *,
    links: list[tuple],
    articles: list[tuple],
    sentiments: dict[int, float],
) -> AsyncMock:
    """Build a mock session routing the three query shapes.

    ``sentiments`` maps article_id → polarity; a missing id yields no sentiment
    Analysis row (so the generator falls back to the per-entity sentiment / 0).
    """
    session = AsyncMock()
    added: list[object] = []
    seq = {"n": 0}

    async def _execute(stmt: object) -> MagicMock:
        text = str(stmt).lower()
        if "from analysis" in text or "analysis." in text:
            # Sentiment lookup — pull the bound article id out of params if we can,
            # else inspect: the test passes a single article per call, so we map
            # by the literal in the compiled statement parameters.
            aid = _bound_article_id(stmt)
            polarity = sentiments.get(aid)
            if polarity is None:
                return _scalar_first_result(None)
            return _scalar_first_result(
                Analysis(
                    target_type="article",
                    target_id=aid,
                    kind="sentiment",
                    provider="test",
                    model="test",
                    result={"polarity": polarity, "label": "x"},
                )
            )
        if "entity_securities" in text:
            return _rows_result(links)
        if "article_entities" in text:
            return _rows_result(articles)
        return _rows_result([])

    def _add(obj: object) -> None:
        added.append(obj)

    async def _flush() -> None:
        for obj in added:
            if isinstance(obj, Signal) and getattr(obj, "id", None) is None:
                seq["n"] += 1
                obj.id = seq["n"]

    session.execute = AsyncMock(side_effect=_execute)
    session.add = MagicMock(side_effect=_add)
    session.flush = AsyncMock(side_effect=_flush)
    session.added = added  # type: ignore[attr-defined]
    return session


def _bound_article_id(stmt: object) -> int:
    """Extract the article id bound into the sentiment lookup's WHERE clause.

    The compiled params include ``target_id`` (the article id) alongside string
    literals and the ``LIMIT`` value; we pick the param whose key references
    ``target_id``.
    """
    try:
        compiled = stmt.compile()  # type: ignore[attr-defined]
        for key, val in compiled.params.items():
            if "target_id" in key and isinstance(val, int):
                return val
    except Exception:
        pass
    return -1


async def test_generate_persists_signal_with_correct_sign() -> None:
    # Security 1 linked to entity 10; two recent positive-sentiment articles.
    links = [(1, 10, 1.0)]
    articles = [
        (1001, _NOW - timedelta(hours=2), None, 10, 0.9, None),
        (1002, _NOW - timedelta(hours=5), 7, 10, 0.8, None),
    ]
    sentiments = {1001: 0.8, 1002: 0.6}
    session = _session(links=links, articles=articles, sentiments=sentiments)

    ids = await generate_signals(session, as_of=_NOW)

    signals = [o for o in session.added if isinstance(o, Signal)]
    assert len(signals) == 1
    assert ids == [signals[0].id]
    sig = signals[0]
    assert sig.security_id == 1
    assert sig.score > 0
    assert sig.direction == "bullish"
    assert 0.0 <= sig.magnitude <= 1.0
    assert 0.0 <= sig.confidence <= 1.0
    assert sorted(sig.supporting_article_ids) == [1001, 1002]
    assert sig.supporting_event_ids == [7]
    assert sig.components["n_articles"] == 2


async def test_generate_negative_sentiment_bearish() -> None:
    links = [(2, 20, 1.0)]
    articles = [(2001, _NOW - timedelta(hours=1), None, 20, 0.9, None)]
    sentiments = {2001: -0.7}
    session = _session(links=links, articles=articles, sentiments=sentiments)

    await generate_signals(session, as_of=_NOW)

    sig = next(o for o in session.added if isinstance(o, Signal))
    assert sig.score < 0
    assert sig.direction == "bearish"


async def test_generate_falls_back_to_entity_sentiment() -> None:
    # No Analysis sentiment row; per-entity ArticleEntity.sentiment used instead.
    links = [(3, 30, 1.0)]
    articles = [(3001, _NOW - timedelta(hours=1), None, 30, 0.9, 0.5)]
    session = _session(links=links, articles=articles, sentiments={})

    await generate_signals(session, as_of=_NOW)

    sig = next(o for o in session.added if isinstance(o, Signal))
    assert sig.score > 0
    assert sig.direction == "bullish"


async def test_generate_skips_security_with_no_recent_articles() -> None:
    links = [(4, 40, 1.0)]
    session = _session(links=links, articles=[], sentiments={})

    ids = await generate_signals(session, as_of=_NOW)

    assert ids == []
    assert not any(isinstance(o, Signal) for o in session.added)


async def test_generate_neutral_when_no_sentiment_anywhere() -> None:
    links = [(5, 50, 1.0)]
    articles = [(5001, _NOW - timedelta(hours=1), None, 50, 0.9, None)]
    session = _session(links=links, articles=articles, sentiments={})

    await generate_signals(session, as_of=_NOW)

    sig = next(o for o in session.added if isinstance(o, Signal))
    # Volume but no direction → neutral, but still persisted (volume present).
    assert sig.score == 0.0
    assert sig.direction == "neutral"
