"""Article-quality tests: sweet-spot length curve, missing fields, DB helper.

Pure functions on synthetic :class:`ArticleFeatures`; ``score_article`` runs
against a mocked :class:`AsyncSession`. No live DB / network.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from unittest.mock import AsyncMock

from newskoo.models.article import Article
from newskoo.quality.article_quality import (
    WEIGHTS,
    ArticleFeatures,
    article_quality,
    quality_components,
    score_article,
)

# A well-formed, mid-length, authored, dated, low-dup article from a decent source.
_GOOD = ArticleFeatures(
    word_count=600,
    has_author=True,
    has_published_at=True,
    language_confidence=0.95,
    title="Central bank holds rates steady as inflation cools through spring",
    near_duplicate=0.0,
    source_credibility=0.8,
)


def test_weights_sum_to_one() -> None:
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def test_good_article_scores_high_and_bounded() -> None:
    score = article_quality(_GOOD)
    assert 0.0 <= score <= 1.0
    assert score > 0.8


def test_sweet_spot_beats_too_short_and_too_long() -> None:
    short = replace(_GOOD, word_count=30)
    long = replace(_GOOD, word_count=8000)
    mid = article_quality(_GOOD)
    assert article_quality(short) < mid
    assert article_quality(long) < mid


def test_length_curve_plateau_and_extremes() -> None:
    def q(n: int) -> float:
        return article_quality(replace(_GOOD, word_count=n))

    # Plateau (600..1500) all score at the top.
    assert q(600) == q(1500) >= q(2000)
    # Monotone climb into the plateau from a stub.
    assert q(10) < q(60) < q(150) < q(400) <= q(600)
    # Monotone decline out of the plateau toward bloat.
    assert q(1500) >= q(3000) >= q(6000) >= q(11000)


def test_missing_author_lowers_score() -> None:
    no_author = replace(_GOOD, has_author=False)
    assert article_quality(no_author) < article_quality(_GOOD)
    # The drop is exactly the has_author weight (component goes 1 → 0).
    assert abs(
        article_quality(_GOOD) - article_quality(no_author) - WEIGHTS["has_author"]
    ) < 1e-9


def test_missing_date_lowers_score() -> None:
    no_date = replace(_GOOD, has_published_at=False)
    assert article_quality(no_date) < article_quality(_GOOD)
    assert abs(
        article_quality(_GOOD) - article_quality(no_date) - WEIGHTS["has_published_at"]
    ) < 1e-9


def test_near_duplicate_penalty_lowers_score() -> None:
    dup = replace(_GOOD, near_duplicate=1.0)
    assert article_quality(dup) < article_quality(_GOOD)


def test_clickbait_title_lowers_quality() -> None:
    clickbait = replace(_GOOD, title="YOU WON'T BELIEVE WHAT HAPPENED NEXT!!!")
    assert article_quality(clickbait) < article_quality(_GOOD)


def test_unknown_source_uses_neutral_prior() -> None:
    no_source = replace(_GOOD, source_credibility=None)
    trusted = replace(_GOOD, source_credibility=1.0)
    untrusted = replace(_GOOD, source_credibility=0.0)
    # Neutral prior sits strictly between fully-trusted and fully-untrusted.
    assert article_quality(untrusted) < article_quality(no_source) < article_quality(trusted)


def test_higher_source_credibility_never_lowers_score() -> None:
    prev = -1.0
    for cred in (0.0, 0.25, 0.5, 0.75, 1.0):
        score = article_quality(replace(_GOOD, source_credibility=cred))
        assert score >= prev - 1e-12
        prev = score


def test_components_reported_and_bounded() -> None:
    comps = quality_components(_GOOD)
    assert set(comps) == set(WEIGHTS)
    assert all(0.0 <= v <= 1.0 for v in comps.values())


# ── async DB helper against a mocked session ────────────────────────────────────


def _mock_session(article: Article | None) -> AsyncMock:
    session = AsyncMock()
    session.get = AsyncMock(return_value=article)
    return session


async def test_score_article_derives_features() -> None:
    article = Article(
        id=42,
        source_id=1,
        canonical_url="https://x.example/a",
        url="https://x.example/a",
        title="Quarterly results beat expectations across the board this year",
        body="body",
        language="en",
        authors=["Jane Doe"],
        published_at=datetime(2026, 5, 1, tzinfo=UTC),
        fetched_at=datetime(2026, 5, 1, tzinfo=UTC),
        content_hash=b"\x00" * 32,
        word_count=700,
    )
    session = _mock_session(article)

    score = await score_article(session, 42, source_credibility=0.9)
    assert 0.0 <= score <= 1.0
    assert score > 0.8
    session.get.assert_awaited_once_with(Article, 42)


async def test_score_article_missing_returns_zero() -> None:
    session = _mock_session(None)
    assert await score_article(session, 999) == 0.0


async def test_score_article_without_author_or_date_is_lower() -> None:
    full = Article(
        id=1,
        source_id=1,
        canonical_url="https://x.example/1",
        url="https://x.example/1",
        title="A perfectly reasonable and adequately long news headline here",
        body="b",
        language="en",
        authors=["A. Writer"],
        published_at=datetime(2026, 5, 1, tzinfo=UTC),
        fetched_at=datetime(2026, 5, 1, tzinfo=UTC),
        content_hash=b"\x00" * 32,
        word_count=600,
    )
    bare = Article(
        id=2,
        source_id=1,
        canonical_url="https://x.example/2",
        url="https://x.example/2",
        title="A perfectly reasonable and adequately long news headline here",
        body="b",
        language=None,
        authors=[],
        published_at=None,
        fetched_at=datetime(2026, 5, 1, tzinfo=UTC),
        content_hash=b"\x00" * 32,
        word_count=600,
    )

    full_session = _mock_session(full)
    bare_session = _mock_session(bare)
    full_score = await score_article(full_session, 1, source_credibility=0.7)
    bare_score = await score_article(bare_session, 2, source_credibility=0.7)
    assert bare_score < full_score
