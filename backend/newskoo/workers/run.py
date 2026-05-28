"""Worker entrypoint: ``python -m newskoo.workers.run <stage>``.

Stages are Kafka consumer groups implemented in later phases:
  parser   — raw.documents  → parsed.articles            (Phase 4)
  dedup    — parsed.articles → dedup.events + persist     (Phase 5)
  analyzer — analyze.requests→ analyze.results            (Phase 6)
  issues   — analyze.results → issues.alerts              (Phase 6)
  scheduler— APScheduler crawl scheduling                 (Phase 3)

Until those land, unknown/未実装 stages exit with a clear message.
"""

from __future__ import annotations

import asyncio
import sys

from newskoo.core.logging import configure_logging, get_logger

log = get_logger(__name__)

STAGES = {"parser", "dedup", "analyzer", "issues", "scheduler"}


async def _run(stage: str) -> None:
    # Dispatch is wired up as each stage is implemented, e.g.:
    #   if stage == "parser":
    #       from newskoo.parse.worker import run as run_parser
    #       await run_parser()
    log.warning("worker.stage_not_implemented", stage=stage)
    raise SystemExit(f"stage '{stage}' not implemented yet")


def main() -> None:
    configure_logging()
    if len(sys.argv) < 2 or sys.argv[1] not in STAGES:
        raise SystemExit(f"usage: python -m newskoo.workers.run {{{'|'.join(sorted(STAGES))}}}")
    asyncio.run(_run(sys.argv[1]))


if __name__ == "__main__":
    main()
