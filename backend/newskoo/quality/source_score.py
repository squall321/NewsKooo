"""Source credibility scoring.

A source's *credibility* is a bounded ``[0, 1]`` summary of how trustworthy and
substantive an outlet has proven to be, derived entirely from **observable
operational signals** the pipeline already collects — never from editorial
opinion. It feeds search/trend ranking and the financial-signal layer as a
multiplicative prior on each article's weight.

Signals & rationale
--------------------
Five features, each individually squashed into ``[0, 1]`` and combined as a
weighted sum (weights in :data:`WEIGHTS`, sum to 1.0). Every feature is oriented
so that "more is better", which makes the composite **monotonic** in each good
feature (raising one, others fixed, never lowers the score):

==================  ======  ==========================================================
feature             weight  meaning / why it signals credibility
==================  ======  ==========================================================
success_rate        0.30    fraction of fetches that succeeded (``1 - error_rate``).
                            A site we can reliably crawl is operationally healthy and
                            consistently publishes well-formed pages. Headline signal.
corroboration_rate  0.25    share of the source's articles whose *event* is
                            multi-source. Stories an outlet reports that independent
                            outlets also report are, on aggregate, more trustworthy
                            than scoops no one else carries.
longevity           0.20    age of the source in the registry, saturating over years.
                            Long-lived outlets have a track record; brand-new ones are
                            unproven (not bad — just lower prior).
volume              0.15    output volume (article count), log-saturated. A source
                            that publishes steadily is a substantive contributor;
                            heavily diminishing returns so a firehose can't dominate.
error_rate_penalty  0.10    explicit penalty term ``1 - error_rate``. Overlaps with
                            success_rate by design: persistent fetch errors are double
                            counted (small extra weight) so flaky sources are pushed
                            down harder.
==================  ======  ==========================================================

All saturating curves are monotonic non-decreasing in their good input, so the
weighted sum is monotonic in success_rate, corroboration_rate, longevity and
volume, and monotonic *non-increasing* in error_rate. The result is clamped to
``[0, 1]`` (the weighted sum of values in ``[0, 1]`` with weights summing to 1
already lies in ``[0, 1]``; the clamp guards against float drift).

``numpy``-free: plain arithmetic, no new deps.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from newskoo.core.logging import get_logger
from newskoo.models.article import Article
from newskoo.models.event import Event
from newskoo.models.source import Source

log = get_logger(__name__)

# ── blend weights (sum to 1.0) ───────────────────────────────────────────────────
WEIGHTS: dict[str, float] = {
    "success_rate": 0.30,  # reliable, well-formed fetches — headline signal
    "corroboration": 0.25,  # share of articles in multi-source events
    "longevity": 0.20,  # track record (age), saturating over years
    "volume": 0.15,  # output volume, log-saturated
    "error_penalty": 0.10,  # explicit extra penalty for fetch errors
}

# Article count at which the log-saturated volume term reaches ~0.5. With
# ``log1p(count) / log1p(2 * V50)`` this gives 0.5 at ``count == V50`` and
# approaches 1.0 with strong diminishing returns above it.
_VOLUME_V50 = 200.0
# Source age (in days) at which longevity reaches ~0.63 (one time-constant of an
# exponential saturation ``1 - exp(-age / tau)``). ~2 years.
_LONGEVITY_TAU_DAYS = 730.0


def _saturate_volume(article_count: int) -> float:
    """Log-saturated output volume in ``[0, 1]``, monotonic non-decreasing.

    ``log1p(n) / log1p(2 * V50)`` is 0 at ``n == 0``, ~0.5 at ``n == V50``, and
    rises toward 1.0 with heavy diminishing returns, so a high-volume firehose
    cannot dominate the composite. Clamped at 1.0 for very large ``n``.
    """
    n = max(0, int(article_count))
    if n == 0:
        return 0.0
    return min(1.0, math.log1p(n) / math.log1p(2.0 * _VOLUME_V50))


def _saturate_longevity(age_days: float) -> float:
    """Exponential-saturation longevity in ``[0, 1]``, monotonic non-decreasing.

    ``1 - exp(-age / tau)`` — 0 for a brand-new source, ~0.63 at one time-constant
    (~2 years), approaching 1.0 for long-established outlets. Negative ages
    (clock skew) clamp to 0.
    """
    age = max(0.0, float(age_days))
    return 1.0 - math.exp(-age / _LONGEVITY_TAU_DAYS)


@dataclass(frozen=True)
class SourceFeatures:
    """Observable, pre-extracted features for :func:`source_credibility`.

    All raw (un-squashed) signals; :func:`source_credibility` normalises each.
    Build them yourself for unit tests, or derive them from the DB via
    :func:`compute_source_scores`.
    """

    success_rate: float  # fraction of fetches that succeeded, in [0, 1]
    error_rate: float  # fraction of fetches that failed, in [0, 1]
    age_days: float  # age of the source in the registry, in days
    article_count: int  # total articles attributed to the source
    corroboration_rate: float  # share of its articles in multi-source events, [0, 1]


def _components(features: SourceFeatures) -> dict[str, float]:
    """Squash each raw feature into ``[0, 1]`` (see module docstring)."""
    success = min(1.0, max(0.0, features.success_rate))
    error = min(1.0, max(0.0, features.error_rate))
    corroboration = min(1.0, max(0.0, features.corroboration_rate))
    return {
        "success_rate": success,
        "corroboration": corroboration,
        "longevity": _saturate_longevity(features.age_days),
        "volume": _saturate_volume(features.article_count),
        # Good = few errors, so the component is ``1 - error_rate``.
        "error_penalty": 1.0 - error,
    }


def source_credibility(features: SourceFeatures) -> float:
    """Composite source credibility in ``[0, 1]`` (higher = more credible).

    Weighted sum of the five normalised components (see :data:`WEIGHTS` and the
    module docstring). Monotonic non-decreasing in ``success_rate``,
    ``corroboration_rate``, ``age_days`` and ``article_count``, and monotonic
    non-increasing in ``error_rate``. Clamped to ``[0, 1]``.
    """
    components = _components(features)
    score = sum(WEIGHTS[name] * value for name, value in components.items())
    return float(min(1.0, max(0.0, score)))


def credibility_components(features: SourceFeatures) -> dict[str, float]:
    """Per-component normalised breakdown (pre-weight) for explainability/UI."""
    return {name: round(value, 6) for name, value in _components(features).items()}


def _features_from_source(
    source: Source,
    *,
    article_count: int,
    corroborated_count: int,
    now: datetime,
) -> SourceFeatures:
    """Derive :class:`SourceFeatures` from a :class:`Source` row + counts.

    Reads success/error from ``Source.health`` (maintained by ingestion: keys
    ``total``, ``fails``, ``error_rate``). ``age_days`` comes from
    ``created_at``; ``corroboration_rate`` is ``corroborated / article_count``.
    """
    health = dict(source.health or {})
    total = int(health.get("total", 0) or 0)
    if total > 0:
        # Trust the explicit error_rate if present, else derive from counts.
        error_rate = float(health.get("error_rate", health.get("fails", 0) / total))
    else:
        # No fetch history: neutral-low prior (treat as unproven, not failing).
        error_rate = 0.0
    error_rate = min(1.0, max(0.0, error_rate))
    success_rate = 1.0 - error_rate if total > 0 else 0.0

    created = source.created_at
    if created is not None and created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    age_days = (now - created).total_seconds() / 86400.0 if created is not None else 0.0

    corroboration_rate = corroborated_count / article_count if article_count > 0 else 0.0

    return SourceFeatures(
        success_rate=success_rate,
        error_rate=error_rate,
        age_days=age_days,
        article_count=article_count,
        corroboration_rate=min(1.0, max(0.0, corroboration_rate)),
    )


async def compute_source_scores(session: AsyncSession) -> dict[int, float]:
    """Compute every source's credibility and merge it into ``Source.health``.

    Derives features per source:

    * **success/error** — from ``Source.health`` (``total``/``fails``/``error_rate``),
      already maintained by the ingestion layer.
    * **volume** — ``count(articles)`` grouped by ``source_id``.
    * **corroboration** — count of the source's articles whose ``event`` has
      ``source_count > 1`` (a multi-source event), divided by its article count.
    * **longevity** — ``now - Source.created_at``.

    Writes the score into ``Source.health['credibility']`` (a *merge* — the rest
    of the health blob is preserved) and ``Source.health['credibility_at']``.
    Flushes so the change is visible in the unit of work, but **does not commit**
    (the caller's ``session_scope`` owns the transaction).

    Returns ``{source_id: credibility}`` for all sources.
    """
    now = datetime.now(UTC)

    # Article volume per source.
    volume_stmt = select(Article.source_id, func.count(Article.id)).group_by(
        Article.source_id
    )
    volume_rows = (await session.execute(volume_stmt)).all()
    volume: dict[int, int] = {int(sid): int(cnt) for sid, cnt in volume_rows if sid is not None}

    # Corroborated articles per source: articles joined to a multi-source event.
    corroborated_stmt = (
        select(Article.source_id, func.count(Article.id))
        .join(Event, Article.event_id == Event.id)
        .where(Event.source_count > 1)
        .group_by(Article.source_id)
    )
    corroborated_rows = (await session.execute(corroborated_stmt)).all()
    corroborated: dict[int, int] = {
        int(sid): int(cnt) for sid, cnt in corroborated_rows if sid is not None
    }

    sources = (await session.execute(select(Source))).scalars().all()

    scores: dict[int, float] = {}
    for source in sources:
        sid = int(source.id)
        features = _features_from_source(
            source,
            article_count=volume.get(sid, 0),
            corroborated_count=corroborated.get(sid, 0),
            now=now,
        )
        score = source_credibility(features)
        scores[sid] = score

        # Merge into health without clobbering the rest of the blob.
        health = dict(source.health or {})
        health["credibility"] = round(score, 6)
        health["credibility_at"] = now.isoformat()
        source.health = health

    await session.flush()
    log.info("source.credibility.computed", sources=len(scores))
    return scores


__all__ = [
    "WEIGHTS",
    "SourceFeatures",
    "compute_source_scores",
    "credibility_components",
    "source_credibility",
]
