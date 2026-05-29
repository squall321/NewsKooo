"""Near-duplicate detection over recent articles via 64-bit SimHash.

The dedup stage compares an incoming article's SimHash against a sliding window
of recently-persisted articles. Two articles are *near-duplicates* when the
Hamming distance between their SimHashes is ``<= settings.dedup_hamming_threshold``
(default 3) — this catches re-syndicated wire copy, near-identical reposts, and
minor editorial revisions while leaving genuinely distinct stories apart.

Distance computation prefers the batched C++ primitives (``newskoo_native``):
``nearest`` for the closest hash and ``hamming_table`` to enumerate every
in-window match. When the native module is absent it falls back to the
pure-Python :func:`newskoo.core.accel.hamming` in a loop, so behaviour is
identical whether or not the extension is built.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from newskoo.core import accel
from newskoo.core.config import get_settings
from newskoo.core.logging import get_logger
from newskoo.models.article import Article

log = get_logger(__name__)

_MASK64 = (1 << 64) - 1

try:  # pragma: no cover - presence depends on the compiled extension
    import newskoo_native as _native  # type: ignore

    _HAVE_NATIVE = True
except ImportError:  # pragma: no cover
    _native = None
    _HAVE_NATIVE = False


@dataclass(slots=True)
class NearDuplicateResult:
    """Outcome of a near-duplicate scan (drives a :class:`DedupEvent`)."""

    is_duplicate: bool
    min_distance: int
    near_duplicate_ids: list[int] = field(default_factory=list)


def _hamming_table(query: int, others: list[int]) -> list[int]:
    """Distances from ``query`` to each hash in ``others`` (native or fallback)."""
    if not others:
        return []
    if _HAVE_NATIVE:
        return [int(d) for d in _native.hamming_table(query, others)]
    return [accel.hamming(query, h) for h in others]


async def _recent_simhashes(
    session: AsyncSession,
    *,
    exclude_canonical_url: str,
    window: int,
) -> list[tuple[int, int]]:
    """Most-recent ``(article_id, simhash)`` rows with a non-null SimHash.

    Ordered by ``id`` descending (a monotonic proxy for recency) and capped at
    ``window`` so the comparison set stays bounded regardless of corpus size.
    The just-persisted article is excluded by its ``canonical_url`` so a row
    never matches itself.
    """
    stmt = (
        select(Article.id, Article.simhash)
        .where(
            Article.simhash.is_not(None),
            Article.canonical_url != exclude_canonical_url,
        )
        .order_by(Article.id.desc())
        .limit(window)
    )
    res = await session.execute(stmt)
    return [(int(row[0]), int(row[1])) for row in res.all()]


async def find_near_duplicate(
    session: AsyncSession,
    art_simhash: int | None,
    canonical_url: str,
    *,
    window: int = 500,
) -> NearDuplicateResult:
    """Scan recent articles for near-duplicates of ``art_simhash``.

    Returns a :class:`NearDuplicateResult`. ``is_duplicate`` is True when the
    closest in-window SimHash is within ``settings.dedup_hamming_threshold``;
    ``near_duplicate_ids`` lists every in-window article at or under that
    threshold (closest first). A ``None``/absent SimHash short-circuits to a
    non-duplicate result (nothing to compare).
    """
    if art_simhash is None:
        return NearDuplicateResult(is_duplicate=False, min_distance=64)

    query = int(art_simhash) & _MASK64
    rows = await _recent_simhashes(
        session, exclude_canonical_url=canonical_url, window=window
    )
    if not rows:
        return NearDuplicateResult(is_duplicate=False, min_distance=64)

    ids = [aid for aid, _ in rows]
    hashes = [h & _MASK64 for _, h in rows]
    distances = _hamming_table(query, hashes)

    threshold = get_settings().dedup_hamming_threshold
    matches = sorted(
        ((dist, aid) for aid, dist in zip(ids, distances, strict=True) if dist <= threshold),
        key=lambda pair: pair[0],
    )
    min_distance = min(distances) if distances else 64
    near_ids = [aid for _dist, aid in matches]

    if near_ids:
        log.info(
            "dedup.near_duplicate",
            canonical_url=canonical_url,
            min_distance=min_distance,
            matches=len(near_ids),
        )
    return NearDuplicateResult(
        is_duplicate=bool(near_ids),
        min_distance=min_distance,
        near_duplicate_ids=near_ids,
    )
