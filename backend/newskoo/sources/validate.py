"""Validate seed-source coverage against the live web.

    uv run python -m newskoo.sources.validate [--timeout 15] [--concurrency 24]
                                              [--json PATH] [--limit N]

Probes every seeded source concurrently:
- ``rss``  → fetch the feed and parse it; OK iff it returns >= 1 entry.
- ``html`` → reachability check on the homepage (OK iff HTTP < 400).
- ``api``  → not hit here; GDELT is keyless/always-on (OK), NewsAPI is key-gated.

Prints a coverage report (totals + per-method + per-region reachable counts and
the list of broken RSS feeds with the reason) and optionally writes JSON. This
is the empirical answer to "how many sites can we actually see". Requires
outbound network; needs no DB/Kafka.
"""

from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from dataclasses import asdict, dataclass

import feedparser
import httpx

from newskoo.sources.seeds import SEED_SOURCES

_UA = "NewsKooBot/0.1 (+https://github.com/squall321/NewsKooo)"


@dataclass
class Probe:
    name: str
    region: str
    fetch_method: str
    target: str
    status: int | None
    ok: bool
    entries: int
    reason: str


async def _probe(client: httpx.AsyncClient, sem: asyncio.Semaphore, src: dict) -> Probe:
    name = src.get("name", "?")
    region = src.get("region", "?")
    method = src.get("fetch_method", "?")
    api_kind = src.get("api_kind")

    if method == "api":
        ok = api_kind == "gdelt"
        reason = "api: gdelt (keyless)" if ok else f"api: {api_kind} (needs key)"
        return Probe(name, region, method, api_kind or "api", None, ok, 0, reason)

    target = src.get("feed_url") or src.get("homepage_url") or ""
    async with sem:
        try:
            resp = await client.get(target, headers={"User-Agent": _UA})
        except Exception as exc:  # report, never crash the sweep
            return Probe(name, region, method, target, None, False, 0, f"error: {type(exc).__name__}")

    status = resp.status_code
    if status >= 400:
        return Probe(name, region, method, target, status, False, 0, f"http {status}")
    if method == "rss":
        feed = feedparser.parse(resp.content)
        n = len(feed.entries)
        return Probe(name, region, method, target, status, n > 0, n, "ok" if n > 0 else "0 entries / unparseable")
    return Probe(name, region, method, target, status, True, 0, "reachable")


async def run(sources: list[dict], *, request_timeout: float, concurrency: int) -> list[Probe]:
    sem = asyncio.Semaphore(concurrency)
    limits = httpx.Limits(max_connections=concurrency)
    async with httpx.AsyncClient(
        timeout=request_timeout, follow_redirects=True, limits=limits
    ) as client:
        return list(await asyncio.gather(*(_probe(client, sem, s) for s in sources)))


def report(probes: list[Probe]) -> dict:
    total = len(probes)
    by_method: Counter[str] = Counter(p.fetch_method for p in probes)
    ok_by_method: Counter[str] = Counter(p.fetch_method for p in probes if p.ok)
    ok = sum(1 for p in probes if p.ok)
    rss = [p for p in probes if p.fetch_method == "rss"]
    rss_ok = [p for p in rss if p.ok]
    broken = [p for p in rss if not p.ok]
    regions_ok = len({p.region for p in probes if p.ok})

    print("\n================ NewsKoo source coverage ================")
    print(f"sources probed   : {total}")
    print(f"reachable/usable : {ok}  ({ok * 100 // max(total, 1)}%)")
    print(f"distinct regions reachable: {regions_ok}")
    for method in sorted(by_method):
        print(f"  {method:4} : {ok_by_method[method]:3}/{by_method[method]:<3} ok")
    print(f"\nRSS feeds live with entries: {len(rss_ok)}/{len(rss)}")
    total_entries = sum(p.entries for p in rss_ok)
    print(f"total RSS entries seen right now: {total_entries}")
    if broken:
        print(f"\n--- broken RSS feeds ({len(broken)}) ---")
        for p in sorted(broken, key=lambda x: x.region):
            print(f"  [{p.region:6}] {p.name[:38]:38} {p.reason:22} {p.target[:60]}")
    return {
        "total": total,
        "ok": ok,
        "by_method": dict(by_method),
        "ok_by_method": dict(ok_by_method),
        "rss_total": len(rss),
        "rss_ok": len(rss_ok),
        "rss_entries_now": total_entries,
        "regions_reachable": regions_ok,
        "broken": [asdict(p) for p in broken],
    }


async def _main(args: argparse.Namespace) -> dict:
    sources = SEED_SOURCES[: args.limit] if args.limit else SEED_SOURCES
    probes = await run(sources, request_timeout=args.timeout, concurrency=args.concurrency)
    return report(probes)


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe seed-source live coverage")
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--concurrency", type=int, default=24)
    parser.add_argument("--limit", type=int, default=0, help="probe only the first N (0=all)")
    parser.add_argument("--json", default="", help="write the summary JSON here")
    args = parser.parse_args()
    summary = asyncio.run(_main(args))
    if args.json:
        import json
        from pathlib import Path

        Path(args.json).write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")
    raise SystemExit(0 if summary["ok"] > 0 else 1)


if __name__ == "__main__":
    main()
