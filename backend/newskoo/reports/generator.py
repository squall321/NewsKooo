"""Query-driven, cited intelligence report generation.

Pulls the relevant recent articles/events for a :class:`ReportQuery`, builds a
compact multilingual context, asks the configured LLM to synthesize a markdown
report with inline citations, and (optionally) persists a :class:`Report` row.

The API's reports router lazily imports :func:`generate_report`; keep that name
stable.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from newskoo.core.logging import get_logger
from newskoo.llm import ChatMessage, LLMProvider, Role, get_provider
from newskoo.models.analysis import Report
from newskoo.models.article import Article
from newskoo.models.event import Event
from newskoo.reports.schemas import Citation, ReportQuery, ReportResult

log = get_logger(__name__)

_SYSTEM = (
    "You are NewsKoo's senior intelligence analyst. From the supplied SOURCES "
    "(news articles and clustered events, possibly in several languages), write a "
    "concise, decision-useful markdown report. Structure it as: a one-paragraph "
    "**Executive summary**, **Key developments** (bullets), **Signals & "
    "implications** (what it means, e.g. for markets/sectors), and **Watch items**. "
    "Reason across languages; do not translate verbatim. Cite every concrete claim "
    "inline using the bracket ids shown in SOURCES, e.g. [A123] for an article or "
    "[E45] for an event. Be specific and neutral; never invent facts or ids."
)

_MAX_BODY_CHARS = 1200  # per-article body budget in the prompt


def _derive_title(q: ReportQuery) -> str:
    if q.title:
        return q.title
    bits: list[str] = []
    if q.keywords:
        bits.append(", ".join(q.keywords[:4]))
    if q.sector:
        bits.append(q.sector)
    if q.region:
        bits.append(q.region)
    scope = " · ".join(bits) if bits else "Global news"
    return f"NewsKoo report: {scope} (last {q.window_hours}h)"


async def _gather(
    session: AsyncSession, q: ReportQuery
) -> tuple[list[Article], list[Event]]:
    since = datetime.now(UTC) - timedelta(hours=q.window_hours)

    art_stmt = select(Article).where(Article.published_at >= since)
    if q.keywords:
        tsquery = " OR ".join(q.keywords)
        art_stmt = art_stmt.where(
            Article.tsv.op("@@")(func.websearch_to_tsquery("simple", tsquery))
        )
    art_stmt = art_stmt.order_by(Article.published_at.desc()).limit(
        max(1, q.max_events * q.max_articles_per_event)
    )
    articles = list((await session.execute(art_stmt)).scalars().all())

    evt_stmt = (
        select(Event)
        .where(Event.last_seen_at >= since)
        .order_by(Event.score.desc())
        .limit(q.max_events)
    )
    events = list((await session.execute(evt_stmt)).scalars().all())
    return articles, events


def _build_context(articles: list[Article], events: list[Event]) -> str:
    lines: list[str] = []
    if events:
        lines.append("## Events")
        for e in events:
            lines.append(f"[E{e.id}] {e.title} (score={e.score:.2f})")
            if e.summary:
                lines.append(f"    {e.summary[:300]}")
    if articles:
        lines.append("\n## Articles")
        for a in articles:
            when = a.published_at.isoformat() if a.published_at else "?"
            lang = a.language or "?"
            body = (a.body or "")[:_MAX_BODY_CHARS]
            lines.append(f"[A{a.id}] ({lang}, {when}) {a.title}\n    {body}")
    return "\n".join(lines) if lines else "(no matching sources in window)"


async def generate_report(
    session: AsyncSession,
    query: ReportQuery | dict,
    *,
    provider: LLMProvider | None = None,
    scheduled: bool = False,
    persist: bool = True,
) -> ReportResult:
    """Generate (and optionally persist) a cited markdown report for ``query``.

    ``query`` may be a :class:`ReportQuery` or a plain mapping (e.g. the API's
    ``ReportRequest.to_query()`` payload), which is coerced/validated.
    """
    if not isinstance(query, ReportQuery):
        query = ReportQuery.model_validate(query)
    articles, events = await _gather(session, query)
    context = _build_context(articles, events)

    prov = provider or get_provider()
    user = (
        f"QUERY: keywords={query.keywords} sector={query.sector} "
        f"region={query.region} window_hours={query.window_hours}\n\n"
        f"SOURCES:\n{context}"
    )
    messages = [
        ChatMessage(role=Role.SYSTEM, content=_SYSTEM, cache=True),
        ChatMessage(role=Role.USER, content=user),
    ]
    resp = await prov.chat(messages)

    title = _derive_title(query)
    citations = Citation(articles=[a.id for a in articles], events=[e.id for e in events])

    report_id: int | None = None
    if persist:
        report = Report(
            query=query.model_dump(mode="json"),
            title=title,
            body_md=resp.text,
            citations=citations.model_dump(),
            provider=resp.provider,
            model=resp.model,
            scheduled=scheduled,
            version=1,
        )
        session.add(report)
        await session.flush()
        report_id = report.id
        log.info(
            "report.generated",
            report_id=report_id,
            articles=len(articles),
            events=len(events),
            provider=resp.provider,
        )

    return ReportResult(
        id=report_id,
        title=title,
        body_md=resp.text,
        citations=citations,
        provider=resp.provider,
        model=resp.model,
        scheduled=scheduled,
        created_at=datetime.now(UTC),
    )
