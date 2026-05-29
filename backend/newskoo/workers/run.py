"""Worker entrypoint: ``python -m newskoo.workers.run <stage>``.

Each stage is a long-running Kafka consumer group (or a scheduled loop) that
exposes ``async def run()``. Stages and their data flow:

  ingest    APScheduler crawl scheduling      → raw.documents      (Phase 3)
  parser    raw.documents   → parsed.articles                      (Phase 4)
  persist   parsed.articles → DB + dedup.events + analyze.requests  (Phase 5)
  results   analyze.results → DB analysis + event clustering        (Phase 5)
  analyzer  analyze.requests→ analyze.results                       (Phase 6)
  issues    (scheduled DB scan) → issues.alerts                     (Phase 6)
"""

from __future__ import annotations

import asyncio
import importlib
import sys

from newskoo.core.logging import configure_logging, get_logger

log = get_logger(__name__)

# stage name → "module:async-callable" exposing run()
STAGES: dict[str, str] = {
    "ingest": "newskoo.ingest.worker:run",
    "parser": "newskoo.parse.worker:run",
    "persist": "newskoo.storage.persist_worker:run",
    "results": "newskoo.storage.results_worker:run",
    "analyzer": "newskoo.analyze.worker:run",
    "issues": "newskoo.analyze.issues_worker:run",
}


async def _run(stage: str) -> None:
    module_path, _, attr = STAGES[stage].partition(":")
    module = importlib.import_module(module_path)
    run_fn = getattr(module, attr)
    log.info("worker.start", stage=stage)
    await run_fn()


def main() -> None:
    configure_logging()
    if len(sys.argv) < 2 or sys.argv[1] not in STAGES:
        raise SystemExit(f"usage: python -m newskoo.workers.run {{{'|'.join(STAGES)}}}")
    try:
        asyncio.run(_run(sys.argv[1]))
    except KeyboardInterrupt:
        log.info("worker.interrupted", stage=sys.argv[1])


if __name__ == "__main__":
    main()
