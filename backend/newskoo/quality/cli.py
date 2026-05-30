"""CLI: recompute source credibility scores.

    uv run python -m newskoo.quality.cli

Writes each source's score into ``Source.health['credibility']`` so search,
trends, and the signal layer can weight by it. Requires a live, migrated DB.
"""

from __future__ import annotations

import asyncio

from newskoo.core.db import dispose_engine, session_scope
from newskoo.core.logging import configure_logging, get_logger
from newskoo.quality.source_score import compute_source_scores

log = get_logger(__name__)


async def _main() -> int:
    async with session_scope() as session:
        scores = await compute_source_scores(session)
    await dispose_engine()
    return len(scores)


def main() -> None:
    configure_logging()
    count = asyncio.run(_main())
    log.info("sources.scored", count=count)
    print(f"scored {count} sources")


if __name__ == "__main__":
    main()
