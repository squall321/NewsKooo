"""CLI: seed the worldwide source catalog into the database.

Usage (DB must be up + migrated)::

    uv run python -m newskoo.sources.seed_cli

Idempotent — safe to re-run (upserts by feed_url else homepage_url).
"""

from __future__ import annotations

import asyncio

from newskoo.core.db import dispose_engine, session_scope
from newskoo.core.logging import configure_logging, get_logger
from newskoo.sources.seeds import seed_sources

log = get_logger(__name__)


async def _main() -> int:
    async with session_scope() as session:
        count = await seed_sources(session)
    await dispose_engine()
    return count


def main() -> None:
    configure_logging()
    count = asyncio.run(_main())
    log.info("sources.seeded", count=count)
    print(f"seeded {count} sources")


if __name__ == "__main__":
    main()
