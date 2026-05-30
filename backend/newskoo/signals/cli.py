"""CLI for the financial signal layer.

    uv run python -m newskoo.signals.cli seed       # seed the securities catalog
    uv run python -m newskoo.signals.cli link       # link entities -> securities
    uv run python -m newskoo.signals.cli generate   # generate signals from recent news
    uv run python -m newskoo.signals.cli all        # seed + link + generate

Requires a live, migrated DB (alembic incl. revision 0002).
"""

from __future__ import annotations

import argparse
import asyncio

from newskoo.core.db import dispose_engine, session_scope
from newskoo.core.logging import configure_logging, get_logger
from newskoo.signals import (
    generate_signals,
    link_entities_to_securities,
    seed_securities,
)

log = get_logger(__name__)


async def _run(command: str) -> None:
    if command in ("seed", "all"):
        async with session_scope() as session:
            n = await seed_securities(session)
        log.info("securities.seeded", count=n)
        print(f"seeded {n} securities")
    if command in ("link", "all"):
        async with session_scope() as session:
            n = await link_entities_to_securities(session)
        log.info("securities.linked", count=n)
        print(f"linked {n} entity-security pairs")
    if command in ("generate", "all"):
        async with session_scope() as session:
            ids = await generate_signals(session)
        log.info("signals.generated", count=len(ids))
        print(f"generated {len(ids)} signals")
    await dispose_engine()


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="NewsKoo financial signal layer")
    parser.add_argument("command", choices=["seed", "link", "generate", "all"])
    args = parser.parse_args()
    asyncio.run(_run(args.command))


if __name__ == "__main__":
    main()
