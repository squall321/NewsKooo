"""Article search: lexical (FTS), semantic (pgvector), and hybrid.

Modes
-----
- **fts** — PostgreSQL full-text search over the generated ``articles.tsv``
  column: ``tsv @@ websearch_to_tsquery('simple', q)`` ranked by ``ts_rank``.
  ``websearch_to_tsquery`` accepts human query syntax (quotes, ``or``, ``-``)
  and never raises on malformed input, so it is safe for raw user strings.
- **semantic** — embed the query with :func:`embed_text` and order by
  ``embedding <=> :qvec`` (cosine distance) ascending. Rows without an embedding
  (not yet analyzed) are excluded.
- **hybrid** — run both, then merge with Reciprocal Rank Fusion (RRF) so the two
  incomparable score scales combine fairly; ties broken by recency.

All modes share optional ``window`` (hours), ``source_id``, ``language``, and
``topic_id`` filters. The returned ``ArticleOut.score`` carries the relevance
signal (ts_rank for fts, ``1 - distance`` for semantic, fused score for hybrid).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from newskoo.analyze.embeddings import embed_text
from newskoo.api.deps import SessionDep
from newskoo.api.metrics import SEARCH_QUERIES
from newskoo.api.schemas import ArticleOut, SearchMode, SearchRequest
from newskoo.core.logging import get_logger
from newskoo.models.article import Article
from newskoo.models.taxonomy import ArticleTopic

router = APIRouter(prefix="/search", tags=["search"])
log = get_logger(__name__)

# RRF constant (standard default); dampens the contribution of low ranks.
_RRF_K = 60


def _apply_common_filters(stmt: Select, req: SearchRequest) -> Select:
    """Window / source / language / topic filters shared by every mode."""
    if req.window is not None:
        since = datetime.now(UTC) - timedelta(hours=req.window)
        stmt = stmt.where(Article.published_at >= since)
    if req.source_id is not None:
        stmt = stmt.where(Article.source_id == req.source_id)
    if req.language is not None:
        stmt = stmt.where(Article.language == req.language)
    if req.topic_id is not None:
        stmt = stmt.where(
            Article.id.in_(
                select(ArticleTopic.article_id).where(
                    ArticleTopic.topic_id == req.topic_id
                )
            )
        )
    return stmt


def _to_out(article: Article, score: float | None) -> ArticleOut:
    out = ArticleOut.model_validate(article)
    out.score = score
    return out


async def _fts(
    session: AsyncSession, req: SearchRequest, limit: int
) -> list[tuple[Article, float]]:
    tsquery = func.websearch_to_tsquery("simple", req.q)
    rank = func.ts_rank(Article.tsv, tsquery)
    stmt = (
        select(Article, rank.label("rank"))
        .where(Article.tsv.op("@@")(tsquery))
        .order_by(rank.desc(), Article.published_at.desc().nullslast())
        .limit(limit)
    )
    stmt = _apply_common_filters(stmt, req)
    rows = (await session.execute(stmt)).all()
    return [(row[0], float(row[1] or 0.0)) for row in rows]


async def _semantic(
    session: AsyncSession, req: SearchRequest, limit: int
) -> list[tuple[Article, float]]:
    qvec = await embed_text(req.q)
    distance = Article.embedding.cosine_distance(qvec)
    stmt = (
        select(Article, distance.label("distance"))
        .where(Article.embedding.is_not(None))
        .order_by(distance.asc())
        .limit(limit)
    )
    stmt = _apply_common_filters(stmt, req)
    rows = (await session.execute(stmt)).all()
    # Convert cosine distance (0=identical) to a similarity score (1=identical).
    return [(row[0], 1.0 - float(row[1] or 0.0)) for row in rows]


def _rrf_merge(
    fts: list[tuple[Article, float]],
    semantic: list[tuple[Article, float]],
    limit: int,
) -> list[tuple[Article, float]]:
    """Reciprocal Rank Fusion of the two ranked lists keyed by article id."""
    scores: dict[int, float] = {}
    keep: dict[int, Article] = {}
    for ranked in (fts, semantic):
        for rank, (article, _raw) in enumerate(ranked):
            scores[article.id] = scores.get(article.id, 0.0) + 1.0 / (_RRF_K + rank + 1)
            keep.setdefault(article.id, article)
    ordered = sorted(
        keep.values(),
        key=lambda a: (
            scores[a.id],
            a.published_at or datetime.min.replace(tzinfo=UTC),
        ),
        reverse=True,
    )
    return [(a, round(scores[a.id], 6)) for a in ordered[:limit]]


@router.post("", response_model=list[ArticleOut])
async def search(
    req: SearchRequest, session: AsyncSession = SessionDep
) -> list[ArticleOut]:
    SEARCH_QUERIES.labels(req.mode.value).inc()
    log.info("api.search", mode=req.mode.value, q_len=len(req.q), window=req.window)

    if req.mode == SearchMode.FTS:
        results = await _fts(session, req, req.limit)
    elif req.mode == SearchMode.SEMANTIC:
        results = await _semantic(session, req, req.limit)
    else:  # hybrid — overscan each side so the fusion has candidates to merge.
        overscan = min(req.limit * 3, 100)
        fts = await _fts(session, req, overscan)
        semantic = await _semantic(session, req, overscan)
        results = _rrf_merge(fts, semantic, req.limit)

    return [_to_out(article, score) for article, score in results]
