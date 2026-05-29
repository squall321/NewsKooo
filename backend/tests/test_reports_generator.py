"""Report generator tests — fake LLM provider + mocked AsyncSession (no DB/network)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from newskoo.llm.base import ChatMessage, LLMProvider, LLMResponse
from newskoo.models.article import Article
from newskoo.models.event import Event
from newskoo.reports import to_markdown
from newskoo.reports.generator import generate_report
from newskoo.reports.schemas import ReportQuery


class _FakeProvider(LLMProvider):
    name = "fake"

    def __init__(self) -> None:
        self.seen: list[ChatMessage] = []

    async def chat(self, messages, *, model=None, max_tokens=None, temperature=None):
        self.seen = messages
        return LLMResponse(
            text="# Summary\nMarkets moved on [A1]; see event [E10].",
            model="fake-1",
            provider="fake",
        )

    async def extract(self, messages, schema, *, model=None):  # pragma: no cover
        return {}

    async def embed(self, texts, *, model=None):  # pragma: no cover
        raise NotImplementedError


def _result(rows: list[object]) -> MagicMock:
    res = MagicMock()
    res.scalars.return_value.all.return_value = rows
    return res


def _session(articles: list[Article], events: list[Event]) -> AsyncMock:
    session = AsyncMock()
    # _gather issues the article select first, then the event select.
    session.execute.side_effect = [_result(articles), _result(events)]
    session.add = MagicMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def _articles() -> list[Article]:
    return [
        Article(
            id=1,
            title="Chipmaker beats forecasts",
            body="Revenue rose sharply amid AI demand.",
            language="en",
            published_at=datetime(2026, 5, 29, tzinfo=UTC),
        )
    ]


@pytest.fixture
def _events() -> list[Event]:
    return [
        Event(
            id=10,
            title="AI chip supply crunch",
            summary="Multiple outlets report tight supply.",
            score=0.91,
            last_seen_at=datetime(2026, 5, 29, tzinfo=UTC),
        )
    ]


async def test_generate_report_builds_cited_report(_articles, _events) -> None:
    session = _session(_articles, _events)
    provider = _FakeProvider()
    query = ReportQuery(keywords=["chips", "AI"], sector="semiconductors", window_hours=48)

    result = await generate_report(session, query, provider=provider, persist=True)

    assert result.body_md.startswith("# Summary")
    assert result.provider == "fake"
    assert result.citations.articles == [1]
    assert result.citations.events == [10]
    # persisted: a Report row was added + flushed.
    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    # the prompt actually carried the source ids the model is told to cite.
    user_msg = result and provider.seen[-1].content
    assert "[A1]" in user_msg and "[E10]" in user_msg


async def test_generate_report_no_persist_skips_add(_articles, _events) -> None:
    session = _session(_articles, _events)
    result = await generate_report(
        session, ReportQuery(keywords=["x"]), provider=_FakeProvider(), persist=False
    )
    session.add.assert_not_called()
    assert result.id is None


def test_to_markdown_includes_citations(_articles, _events) -> None:
    from newskoo.reports.schemas import Citation, ReportResult

    md = to_markdown(
        ReportResult(
            title="T",
            body_md="Body [A1].",
            citations=Citation(articles=[1], events=[10]),
            provider="fake",
            model="fake-1",
        )
    )
    assert "# T" in md and "A1" in md and "E10" in md and "fake" in md
