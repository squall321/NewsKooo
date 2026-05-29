"""Persist-stage tests against a mocked AsyncSession (no live DB/Redis).

Covers the three idempotency paths of :func:`storage.persist.persist_parsed`:
new insert, content-hash-change → version snapshot, and same-hash no-op. The
Redis fast-path is neutralised by patching the seen-set so tests never touch a
live Redis.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from newskoo.core.accel import content_hash
from newskoo.core.contracts import ParsedArticle
from newskoo.models.article import Article, ArticleVersion
from newskoo.storage import persist


@pytest.fixture(autouse=True)
def _no_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the Redis fast-path a no-op so tests don't need a live Redis."""

    async def _never_seen(canonical_url: str, content_hash_hex: str) -> bool:
        return False

    monkeypatch.setattr(persist, "_maybe_seen_fast_path", _never_seen)


def _session(existing: Article | None) -> AsyncMock:
    """A fake AsyncSession whose first execute() yields ``existing`` (or None).

    ``add`` is sync; ``flush`` assigns a synthetic id to freshly-added Articles.
    """
    session = AsyncMock()
    res = MagicMock()
    res.scalar_one_or_none.return_value = existing
    session.execute = AsyncMock(return_value=res)

    added: list[object] = []

    def _add(obj: object) -> None:
        added.append(obj)

    async def _flush() -> None:
        for obj in added:
            if isinstance(obj, Article) and getattr(obj, "id", None) is None:
                obj.id = 4242

    session.add = MagicMock(side_effect=_add)
    session.flush = AsyncMock(side_effect=_flush)
    session.added = added  # type: ignore[attr-defined]
    return session


def _parsed(body: str = "the city council approved the transit budget") -> ParsedArticle:
    return ParsedArticle(
        source_id=7,
        url="https://x.test/a",
        canonical_url="https://x.test/a",
        title="Transit budget approved",
        body=body,
        language="en",
        authors=["Jane Doe"],
        published_at=datetime(2026, 5, 29, tzinfo=UTC),
        fetched_at=datetime(2026, 5, 29, 8, tzinfo=UTC),
        content_hash=content_hash(body).hex(),
        simhash=12345,
        word_count=7,
    )


async def test_persist_new_insert() -> None:
    session = _session(existing=None)
    art = _parsed()

    article_id, is_new = await persist.persist_parsed(session, art)

    assert is_new is True
    assert article_id == 4242
    inserted = [o for o in session.added if isinstance(o, Article)]
    assert len(inserted) == 1
    row = inserted[0]
    assert row.canonical_url == art.canonical_url
    assert row.status == "parsed"
    assert row.content_hash == bytes.fromhex(art.content_hash)
    assert row.simhash == 12345
    # No version snapshot on a fresh insert.
    assert not [o for o in session.added if isinstance(o, ArticleVersion)]


async def test_persist_content_change_creates_version() -> None:
    old_body = "original body text about the budget"
    existing = Article(
        id=99,
        source_id=7,
        canonical_url="https://x.test/a",
        url="https://x.test/a",
        title="Old title",
        body=old_body,
        language="en",
        fetched_at=datetime(2026, 5, 28, tzinfo=UTC),
        content_hash=content_hash(old_body),
        simhash=111,
        word_count=6,
        status="analyzed",
    )
    session = _session(existing=existing)
    art = _parsed(body="substantially revised body with new transit figures")

    article_id, is_new = await persist.persist_parsed(session, art)

    assert is_new is False
    assert article_id == 99
    # A snapshot of the prior state was appended.
    versions = [o for o in session.added if isinstance(o, ArticleVersion)]
    assert len(versions) == 1
    snap = versions[0]
    assert snap.article_id == 99
    assert snap.title == "Old title"
    assert snap.body == old_body
    assert snap.content_hash == content_hash(old_body)
    # The existing row was updated in place to the new content.
    assert existing.title == art.title
    assert existing.body == art.body
    assert existing.content_hash == bytes.fromhex(art.content_hash)
    assert existing.status == "parsed"


async def test_persist_same_hash_is_noop() -> None:
    body = "identical body content that has not changed at all"
    existing = Article(
        id=55,
        source_id=7,
        canonical_url="https://x.test/a",
        url="https://x.test/a",
        title="Title",
        body=body,
        language="en",
        fetched_at=datetime(2026, 5, 28, tzinfo=UTC),
        content_hash=content_hash(body),
        simhash=222,
        word_count=9,
        status="analyzed",
    )
    session = _session(existing=existing)
    art = _parsed(body=body)

    article_id, is_new = await persist.persist_parsed(session, art)

    assert is_new is False
    assert article_id == 55
    # No version snapshot, no insert, original fields untouched.
    assert not [o for o in session.added if isinstance(o, ArticleVersion)]
    assert not [o for o in session.added if isinstance(o, Article)]
    assert existing.title == "Title"
    assert existing.status == "analyzed"


async def test_write_crawl_log_appends_row() -> None:
    session = _session(existing=None)
    entry = await persist.write_crawl_log(
        session,
        source_id=7,
        url="https://x.test/a",
        method="rss",
        http_status=200,
        bytes_=2048,
        latency_ms=120,
        ok=True,
    )
    assert entry.source_id == 7
    assert entry.ok is True
    assert entry.http_status == 200
    session.flush.assert_awaited()
