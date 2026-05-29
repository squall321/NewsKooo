"""Report generation (Phase 9): query-driven, cited LLM reports over events/
articles; scheduled + on-demand; versioned storage and export."""

from newskoo.reports.export import to_markdown
from newskoo.reports.generator import generate_report
from newskoo.reports.scheduler import build_report_scheduler, run_scheduled_report
from newskoo.reports.schemas import Citation, ReportQuery, ReportResult

__all__ = [
    "Citation",
    "ReportQuery",
    "ReportResult",
    "build_report_scheduler",
    "generate_report",
    "run_scheduled_report",
    "to_markdown",
]
