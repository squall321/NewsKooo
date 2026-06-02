"""Live-verified source-expansion buckets.

Each bucket module in this package exposes ``SOURCES: list[dict]`` of feeds that
were fetched with a desktop-browser User-Agent and confirmed to return a
parseable feed with >= 1 item. They are auto-discovered and concatenated into
``EXTRA_SOURCES``; :mod:`newskoo.sources.seeds` dedup-merges that into
``SEED_SOURCES``. A malformed/empty bucket is skipped (it must never break the
whole catalog). See docs/SOURCE_COVERAGE.md.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any

from newskoo.core.logging import get_logger

log = get_logger(__name__)

EXTRA_SOURCES: list[dict[str, Any]] = []

for _mod in pkgutil.iter_modules(__path__):
    if _mod.name.startswith("_"):
        continue
    try:
        _m = importlib.import_module(f"{__name__}.{_mod.name}")
        _sources = getattr(_m, "SOURCES", None) or []
        EXTRA_SOURCES.extend(_sources)
    except Exception as exc:  # a broken bucket must not break the catalog
        log.warning("extra.bucket_load_failed", bucket=_mod.name, error=str(exc))

__all__ = ["EXTRA_SOURCES"]
