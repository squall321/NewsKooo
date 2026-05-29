"""Near-duplicate detection tests against a mocked AsyncSession (no live DB).

Exercises :func:`cluster.dedup.find_near_duplicate` with the pure-Python accel
fallback (the native batch path is force-disabled so the test is deterministic
regardless of whether the C++ extension is built). Recent simhashes are supplied
via a fake ``execute().all()``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from newskoo.cluster import dedup


@pytest.fixture(autouse=True)
def _force_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force the pure-Python hamming path so results don't depend on the build."""
    monkeypatch.setattr(dedup, "_HAVE_NATIVE", False)


def _session(rows: list[tuple[int, int]]) -> AsyncMock:
    session = AsyncMock()
    res = MagicMock()
    res.all.return_value = rows
    session.execute = AsyncMock(return_value=res)
    return session


async def test_near_duplicate_detected_within_threshold() -> None:
    # Query differs from id=10 by a single bit (distance 1 <= threshold 3).
    query = 0b1010_1010
    rows = [
        (10, 0b1010_1011),  # distance 1 → near-duplicate
        (11, 0b0101_0101),  # far away
    ]
    session = _session(rows)

    out = await dedup.find_near_duplicate(session, query, "https://x.test/a", window=50)

    assert out.is_duplicate is True
    assert out.min_distance == 1
    assert out.near_duplicate_ids == [10]


async def test_distinct_article_not_flagged() -> None:
    query = 0
    rows = [(20, (1 << 40) - 1)]  # 40 bits set → distance 40, way over threshold
    session = _session(rows)

    out = await dedup.find_near_duplicate(session, query, "https://x.test/b", window=50)

    assert out.is_duplicate is False
    assert out.near_duplicate_ids == []
    assert out.min_distance == 40


async def test_multiple_near_dups_sorted_closest_first() -> None:
    query = 0b0000
    rows = [
        (1, 0b0011),  # distance 2
        (2, 0b0001),  # distance 1
        (3, 0b1111),  # distance 4 (over threshold 3)
    ]
    session = _session(rows)

    out = await dedup.find_near_duplicate(session, query, "https://x.test/c", window=50)

    assert out.is_duplicate is True
    assert out.near_duplicate_ids == [2, 1]  # closest first
    assert out.min_distance == 1


async def test_none_simhash_short_circuits() -> None:
    session = _session([(1, 0)])
    out = await dedup.find_near_duplicate(session, None, "https://x.test/d")
    assert out.is_duplicate is False
    assert out.min_distance == 64
    session.execute.assert_not_awaited()


async def test_empty_window_is_not_duplicate() -> None:
    session = _session([])
    out = await dedup.find_near_duplicate(session, 123, "https://x.test/e")
    assert out.is_duplicate is False
    assert out.near_duplicate_ids == []
