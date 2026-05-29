"""Report endpoints: list, detail, and on-demand generation.

Generation delegates to ``newskoo.reports.generator.generate_report`` (Phase 9),
imported lazily so the API runs even before that module lands. If the generator
is unavailable the POST returns ``503 Service Unavailable`` rather than 500.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from newskoo.api.deps import AuthDep, SessionDep
from newskoo.api.routers import LimitQuery, OffsetQuery
from newskoo.api.schemas import Paginated, ReportOut, ReportRequest
from newskoo.core.logging import get_logger
from newskoo.models.analysis import Report

router = APIRouter(prefix="/reports", tags=["reports"])
log = get_logger(__name__)


@router.get("", response_model=Paginated[ReportOut])
async def list_reports(
    session: AsyncSession = SessionDep,
    limit: int = LimitQuery,
    offset: int = OffsetQuery,
) -> Paginated[ReportOut]:
    stmt = select(Report).order_by(Report.created_at.desc(), Report.id.desc())
    rows = (await session.execute(stmt.limit(limit).offset(offset))).scalars().all()
    total = int(await session.scalar(select(func.count()).select_from(Report)) or 0)
    return Paginated[ReportOut](
        items=[ReportOut.model_validate(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(
    report_id: int, session: AsyncSession = SessionDep
) -> ReportOut:
    report = await session.get(Report, report_id)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "report not found")
    return ReportOut.model_validate(report)


def _load_generator() -> Any:
    """Import the Phase-9 report generator lazily; ``None`` if not present."""
    try:
        from newskoo.reports.generator import generate_report  # type: ignore
    except ImportError:
        return None
    return generate_report


@router.post(
    "", response_model=ReportOut, status_code=status.HTTP_201_CREATED, dependencies=[AuthDep]
)
async def generate(
    payload: ReportRequest, session: AsyncSession = SessionDep
) -> ReportOut:
    generate_report = _load_generator()
    if generate_report is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "report generation is not available yet (Phase 9)",
        )
    query = payload.to_query()
    log.info("api.report_generate", query=query)
    result = await generate_report(session, query)
    await session.commit()
    return ReportOut(
        id=result.id,
        query=query,
        title=result.title,
        body_md=result.body_md,
        citations=result.citations.model_dump(),
        provider=result.provider,
        model=result.model,
        scheduled=result.scheduled,
        version=result.version,
        created_at=result.created_at,
    )
