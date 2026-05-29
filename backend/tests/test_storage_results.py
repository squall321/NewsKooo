"""Results-stage tests against a mocked AsyncSession (no live DB).

Covers :func:`storage.results.persist_analysis`: the Analysis audit row plus
kind-specific projections. ``assign_event`` is patched so embedding tests assert
the call without exercising pgvector. Catalog upserts are simulated by a fake
session whose ``execute`` returns "not found" (so a new catalog row is added)
and whose ``get`` returns ``None`` (so a new link row is added).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from newskoo.core.contracts import AnalysisKind, AnalyzeResult
from newskoo.models.analysis import Analysis
from newskoo.models.article import Article
from newskoo.models.taxonomy import (
    ArticleEntity,
    ArticleKeyword,
    ArticleTopic,
    Entity,
    Keyword,
    Topic,
)
from newskoo.storage import results


def _session(article: Article | None) -> AsyncMock:
    """Fake AsyncSession: catalog lookups miss; ``get`` returns the article
    (for status update) but ``None`` for link-row PK lookups."""
    session = AsyncMock()
    added: list[object] = []
    seq = {"n": 0}

    def _add(obj: object) -> None:
        added.append(obj)

    async def _flush() -> None:
        for obj in added:
            if getattr(obj, "id", None) is None and isinstance(obj, Entity | Keyword | Topic):
                seq["n"] += 1
                obj.id = seq["n"]

    # execute() always misses (scalar_one_or_none -> None) → new catalog rows.
    miss = MagicMock()
    miss.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=miss)

    async def _get(model: type, pk: object) -> object | None:
        if model is Article:
            return article
        return None  # link rows (composite PK) are always treated as new

    session.get = AsyncMock(side_effect=_get)
    session.add = MagicMock(side_effect=_add)
    session.flush = AsyncMock(side_effect=_flush)
    session.added = added  # type: ignore[attr-defined]
    return session


def _result(kind: AnalysisKind, result: dict, embedding=None) -> AnalyzeResult:
    return AnalyzeResult(
        target_type="article",
        target_id=42,
        kind=kind,
        provider="local",
        model="bge-m3",
        result=result,
        embedding=embedding,
        tokens=10,
        cost_usd=0.0,
    )


async def test_persist_analysis_writes_analysis_row_and_sets_status() -> None:
    article = Article(id=42, status="parsed")
    session = _session(article)
    res = _result(AnalysisKind.SUMMARY, {"summary": "A concise summary."})

    await results.persist_analysis(session, res)

    rows = [o for o in session.added if isinstance(o, Analysis)]
    assert len(rows) == 1
    assert rows[0].kind == "summary"
    assert rows[0].target_id == 42
    assert article.status == "analyzed"


async def test_entities_upsert_creates_entity_and_link() -> None:
    session = _session(Article(id=42, status="parsed"))
    res = _result(
        AnalysisKind.ENTITIES,
        {
            "entities": [
                {"name": "Acme Corp", "type": "org", "salience": 0.9, "count": 3,
                 "sentiment": -0.2},
                "BareName",  # bare string fallback → type 'unknown'
            ]
        },
    )

    await results.persist_analysis(session, res)

    entities = [o for o in session.added if isinstance(o, Entity)]
    links = [o for o in session.added if isinstance(o, ArticleEntity)]
    assert {e.name for e in entities} == {"Acme Corp", "BareName"}
    assert len(links) == 2
    acme = next(link for link in links if link.entity_id is not None)
    assert acme.salience == 0.9
    assert acme.count == 3
    assert acme.sentiment == -0.2


async def test_keywords_upsert_creates_keyword_and_link() -> None:
    session = _session(Article(id=42, status="parsed"))
    res = _result(
        AnalysisKind.KEYWORDS,
        {"keywords": [{"term": "transit budget", "weight": 0.77}, "subway"]},
    )

    await results.persist_analysis(session, res)

    keywords = [o for o in session.added if isinstance(o, Keyword)]
    links = [o for o in session.added if isinstance(o, ArticleKeyword)]
    assert {k.term for k in keywords} == {"transit budget", "subway"}
    assert len(links) == 2
    assert any(link.weight == 0.77 for link in links)


async def test_topics_upsert_creates_topic_and_link() -> None:
    session = _session(Article(id=42, status="parsed"))
    res = _result(
        AnalysisKind.TOPICS,
        {"topics": [{"slug": "economy-markets", "label": "Markets",
                     "confidence": 0.65}]},
    )

    await results.persist_analysis(session, res)

    topics = [o for o in session.added if isinstance(o, Topic)]
    links = [o for o in session.added if isinstance(o, ArticleTopic)]
    assert len(topics) == 1
    assert topics[0].slug == "economy-markets"
    assert len(links) == 1
    assert links[0].confidence == 0.65


async def test_embedding_sets_article_embedding_and_calls_assign_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    article = Article(id=42, status="parsed")
    session = _session(article)

    calls: list[tuple[int, list[float]]] = []

    async def _fake_assign(sess, article_id: int, embedding: list[float]) -> int:
        calls.append((article_id, embedding))
        return 123

    monkeypatch.setattr(results, "assign_event", _fake_assign)

    vec = [0.1, 0.2, 0.3]
    res = _result(AnalysisKind.EMBEDDING, {}, embedding=vec)

    await results.persist_analysis(session, res)

    assert article.embedding == vec
    assert calls == [(42, vec)]
    assert article.status == "analyzed"


async def test_embedding_missing_vector_skips_assign(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    article = Article(id=42, status="parsed")
    session = _session(article)
    called = False

    async def _fake_assign(*a, **k) -> int:
        nonlocal called
        called = True
        return 0

    monkeypatch.setattr(results, "assign_event", _fake_assign)
    res = _result(AnalysisKind.EMBEDDING, {}, embedding=None)

    await results.persist_analysis(session, res)

    assert called is False
    assert article.embedding is None
