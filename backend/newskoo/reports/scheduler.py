"""Scheduled report generation for saved queries.

Each saved query runs on a cron/interval cadence, generating a fresh report
version. Wire saved queries from config or the DB; here we provide the runner
the API/ops layer schedules.
"""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from newskoo.core.db import session_scope
from newskoo.core.logging import get_logger
from newskoo.reports.generator import generate_report
from newskoo.reports.schemas import ReportQuery

log = get_logger(__name__)


async def run_scheduled_report(query: ReportQuery) -> int | None:
    """Generate one scheduled report for ``query``; returns the new report id."""
    async with session_scope() as session:
        result = await generate_report(session, query, scheduled=True)
    log.info("report.scheduled_run", title=result.title, report_id=result.id)
    return result.id


def build_report_scheduler(
    saved_queries: list[tuple[ReportQuery, int]],
    *,
    scheduler: AsyncIOScheduler | None = None,
) -> AsyncIOScheduler:
    """Schedule each ``(query, every_minutes)`` pair on an interval trigger."""
    sched = scheduler or AsyncIOScheduler(timezone="UTC")
    for idx, (query, every_minutes) in enumerate(saved_queries):
        sched.add_job(
            run_scheduled_report,
            trigger=IntervalTrigger(minutes=max(1, every_minutes)),
            args=[query],
            id=f"report-{idx}",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )
    return sched
