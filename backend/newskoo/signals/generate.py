"""Signal generation — turn recent news into per-security tradeable signals.

This is the stateful orchestrator that ties the pieces together:

    Security ─(EntitySecurity)→ Entity ─(ArticleEntity)→ Article (within window)
                                                    │
                                       sentiment ←─ Analysis(kind='sentiment')
                                                    or ArticleEntity.sentiment

For each security that has at least one linked entity, we gather the recent
articles (published within ``window_hours`` of ``as_of``) mentioning any of its
entities, score each as an :func:`~newskoo.signals.impact.article_impact`
(decayed by recency), aggregate the decayed impacts into one :class:`Signal`,
and persist it.

Aggregation math (mirrors :func:`~newskoo.signals.impact.event_impact`)
-----------------------------------------------------------------------
Let each contributing article *i* have signed impact ``score_i`` and weight
``w_i`` (the article impact's ``confidence`` = strength · recency decay). Then::

    score      = Σ w_i · score_i / Σ w_i          (weight-weighted mean, [-1, 1])
    magnitude  = |score|                          ([0, 1])
    direction  = sign(score) → bullish/bearish/neutral
    confidence = vol_conf · agreement
      vol_conf  = 1 - exp(-Σ w_i / TAU)           (sample-size saturation)
      agreement = |Σ w_i·score_i| / Σ w_i·|score_i|   (1 = unanimous, 0 = cancels)

``confidence`` thus rises with both the *amount* of corroborating recent news
(``vol_conf``) and the *consistency* of its direction (``agreement``): a single
article, or a pile of articles that disagree, yields low confidence.

Sentiment source (graceful degradation, integration point #1 + #3)
-------------------------------------------------------------------
Per article we look for a stored sentiment in this order:

1. ``Analysis`` row with ``kind='sentiment'`` for that article → ``result['polarity']``
   (the analyze stage's document-level sentiment, -1..1).
2. else the per-entity ``ArticleEntity.sentiment`` (entity-directed tone).
3. else neutral (0.0) — the article still contributes *volume* but no direction.

``magnitude`` per article uses the link confidence · the entity salience (how
strongly the article is about this security). ``source_credibility`` is read
from the source if a credibility signal is available (integration point #3);
absent that it defaults to a neutral 0.5, which the impact gate floors anyway.
``novelty`` defaults to 1.0 (full) unless an article carries a novelty hint in
its analysis — dedup/cluster (#2) can lower this later.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from newskoo.core.config import get_settings
from newskoo.core.logging import get_logger
from newskoo.models.analysis import Analysis
from newskoo.models.article import Article
from newskoo.models.finance import EntitySecurity, Security, Signal
from newskoo.models.taxonomy import ArticleEntity
from newskoo.signals.impact import (
    _CONF_TAU,
    article_impact,
)

log = get_logger(__name__)

# Default per-article quality inputs when the upstream signal is unavailable.
_DEFAULT_NOVELTY: float = 1.0
_DEFAULT_CREDIBILITY: float = 0.5


def _direction(score: float) -> str:
    """bullish | bearish | neutral from a signed score (eps guards 0)."""
    if score > 1e-9:
        return "bullish"
    if score < -1e-9:
        return "bearish"
    return "neutral"


def _age_hours(published_at: datetime | None, as_of: datetime) -> float:
    """Hours between ``published_at`` and ``as_of`` (>= 0; missing → 0 = 'now').

    Treats a naive ``published_at`` as UTC so mixing naive/aware timestamps from
    the DB never raises; clamps negatives (future/clock-skew) to 0.
    """
    if published_at is None:
        return 0.0
    pub = published_at
    if pub.tzinfo is None:
        pub = pub.replace(tzinfo=UTC)
    ref = as_of if as_of.tzinfo is not None else as_of.replace(tzinfo=UTC)
    delta = (ref - pub).total_seconds() / 3600.0
    return delta if delta > 0.0 else 0.0


async def _sentiment_for(session: AsyncSession, article_id: int) -> float | None:
    """Document-level sentiment polarity for an article, or ``None``.

    Reads the most recent ``Analysis(kind='sentiment', target_type='article')``
    row and returns its ``result['polarity']`` clamped to [-1, 1].
    """
    stmt = (
        select(Analysis)
        .where(
            Analysis.target_type == "article",
            Analysis.target_id == article_id,
            Analysis.kind == "sentiment",
        )
        .order_by(Analysis.id.desc())
        .limit(1)
    )
    row = (await session.execute(stmt)).scalars().first()
    if row is None:
        return None
    polarity = row.result.get("polarity") if isinstance(row.result, dict) else None
    if polarity is None:
        return None
    val = float(polarity)
    return -1.0 if val < -1.0 else 1.0 if val > 1.0 else val


async def generate_signals(
    session: AsyncSession,
    *,
    window_hours: int | None = None,
    as_of: datetime | None = None,
) -> list[int]:
    """Generate + persist a :class:`Signal` per security with recent linked news.

    Args:
        session: async DB session (transaction owned by the caller; we flush but
            do not commit).
        window_hours: lookback window for contributing articles; defaults to
            ``settings.signal_window_hours`` (72).
        as_of: signal timestamp / window anchor; defaults to ``datetime.now(UTC)``.

    Returns the list of inserted ``Signal`` ids. Securities with no contributing
    article in the window are skipped (no zero-signal rows are written).
    """
    settings = get_settings()
    window = settings.signal_window_hours if window_hours is None else window_hours
    half_life = settings.signal_half_life_hours
    now = as_of if as_of is not None else datetime.now(UTC)
    cutoff = now - timedelta(hours=window)

    # All securities that have at least one linked entity, with their entity ids
    # and link confidences.
    link_stmt = select(
        Security.id, EntitySecurity.entity_id, EntitySecurity.confidence
    ).join(EntitySecurity, EntitySecurity.security_id == Security.id)
    link_rows = (await session.execute(link_stmt)).all()

    # security_id → {entity_id: link_confidence}
    sec_entities: dict[int, dict[int, float]] = {}
    for security_id, entity_id, confidence in link_rows:
        sec_entities.setdefault(int(security_id), {})[int(entity_id)] = float(confidence)

    created: list[int] = []
    for security_id, ent_conf in sec_entities.items():
        entity_ids = list(ent_conf.keys())
        # Recent articles mentioning any linked entity, with the per-entity
        # salience/sentiment from the association row.
        art_stmt = (
            select(
                Article.id,
                Article.published_at,
                Article.event_id,
                ArticleEntity.entity_id,
                ArticleEntity.salience,
                ArticleEntity.sentiment,
            )
            .join(ArticleEntity, ArticleEntity.article_id == Article.id)
            .where(
                ArticleEntity.entity_id.in_(entity_ids),
                Article.published_at.is_not(None),
                Article.published_at >= cutoff,
                Article.published_at <= now,
            )
        )
        art_rows = (await session.execute(art_stmt)).all()
        if not art_rows:
            continue

        # An article may mention several of the security's entities; keep the
        # strongest (highest salience · link confidence) contribution per article.
        best_by_article: dict[int, dict] = {}
        for art_id, published_at, event_id, entity_id, salience, ae_sentiment in art_rows:
            link_conf = ent_conf.get(int(entity_id), 0.0)
            mag = float(salience or 0.0) * link_conf
            prev = best_by_article.get(int(art_id))
            if prev is None or mag > prev["magnitude"]:
                best_by_article[int(art_id)] = {
                    "magnitude": mag,
                    "published_at": published_at,
                    "event_id": int(event_id) if event_id is not None else None,
                    "ae_sentiment": float(ae_sentiment) if ae_sentiment is not None else None,
                }

        # Score each contributing article and accumulate the weighted aggregate.
        sum_w = 0.0
        sum_ws = 0.0  # Σ w_i · score_i
        sum_wabs = 0.0  # Σ w_i · |score_i|
        article_ids: list[int] = []
        event_ids: set[int] = set()
        contrib_components: list[dict] = []

        for art_id, info in best_by_article.items():
            doc_sentiment = await _sentiment_for(session, art_id)
            sentiment = (
                doc_sentiment
                if doc_sentiment is not None
                else (info["ae_sentiment"] if info["ae_sentiment"] is not None else 0.0)
            )
            impact = article_impact(
                sentiment=sentiment,
                magnitude=info["magnitude"],
                novelty=_DEFAULT_NOVELTY,
                source_credibility=_DEFAULT_CREDIBILITY,
                age_hours=_age_hours(info["published_at"], now),
                half_life=half_life,
            )
            w = impact.confidence  # strength · recency decay
            sum_w += w
            sum_ws += w * impact.score
            sum_wabs += w * abs(impact.score)
            article_ids.append(art_id)
            if info["event_id"] is not None:
                event_ids.add(info["event_id"])
            contrib_components.append(
                {"article_id": art_id, "score": impact.score, "weight": w}
            )

        if sum_w <= 0.0:
            # Everything fully decayed / zero-magnitude: no usable signal.
            continue

        score = sum_ws / sum_w
        score = -1.0 if score < -1.0 else 1.0 if score > 1.0 else score
        vol_conf = 1.0 - math.exp(-sum_w / _CONF_TAU)
        agreement = abs(sum_ws) / sum_wabs if sum_wabs > 0.0 else 0.0
        confidence = vol_conf * agreement

        signal = Signal(
            security_id=security_id,
            as_of=now,
            horizon_hours=window,
            score=score,
            direction=_direction(score),
            magnitude=abs(score),
            confidence=confidence,
            components={
                "n_articles": len(article_ids),
                "total_weight": sum_w,
                "vol_confidence": vol_conf,
                "agreement": agreement,
                "contributions": contrib_components,
            },
            supporting_article_ids=sorted(article_ids),
            supporting_event_ids=sorted(event_ids),
        )
        session.add(signal)
        await session.flush()
        created.append(int(signal.id))

    log.info("signals.generate", signals=len(created), window_hours=window)
    return created
