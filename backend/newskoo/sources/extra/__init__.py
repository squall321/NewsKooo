"""Live-verified source-expansion buckets (2026-06-02).

Each bucket module exposes ``SOURCES: list[dict]`` of feeds that were fetched
with a desktop-browser User-Agent and confirmed to return a parseable feed with
>= 1 item. ``EXTRA_SOURCES`` concatenates them; :mod:`newskoo.sources.seeds`
dedup-merges it into ``SEED_SOURCES``. See docs/SOURCE_COVERAGE.md.
"""

from __future__ import annotations

from typing import Any

from newskoo.sources.extra.africa_me import SOURCES as _africa_me
from newskoo.sources.extra.asia import SOURCES as _asia
from newskoo.sources.extra.europe import SOURCES as _europe
from newskoo.sources.extra.finance_tech_niche import SOURCES as _finance_tech_niche
from newskoo.sources.extra.latam import SOURCES as _latam
from newskoo.sources.extra.science import SOURCES as _science

EXTRA_SOURCES: list[dict[str, Any]] = [
    *_asia,
    *_africa_me,
    *_latam,
    *_europe,
    *_science,
    *_finance_tech_niche,
]

__all__ = ["EXTRA_SOURCES"]
