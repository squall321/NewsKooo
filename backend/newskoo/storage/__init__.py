"""Storage persistence stage (Phase 5).

Write path for the structured store and the bridge to clustering/analysis:

* :mod:`newskoo.storage.persist` — idempotent ``parsed.articles`` upserts
  (``canonical_url`` + ``content_hash`` revisioning) and the crawl-log helper.
* :mod:`newskoo.storage.results` — persist ``analyze.results`` as
  :class:`~newskoo.models.analysis.Analysis` rows and project structured kinds
  (entities/keywords/topics/embedding) into catalog + link tables.
* :mod:`newskoo.storage.persist_worker` — Kafka consumer:
  ``parsed.articles`` → DB + ``dedup.events`` + ``analyze.requests``.
* :mod:`newskoo.storage.results_worker` — Kafka consumer:
  ``analyze.results`` → DB (+ clustering).
"""

from newskoo.storage.persist import persist_parsed, write_crawl_log
from newskoo.storage.results import persist_analysis

__all__ = [
    "persist_analysis",
    "persist_parsed",
    "write_crawl_log",
]
