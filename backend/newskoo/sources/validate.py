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

_BOT_UA = "NewsKooBot/0.1 (+https://github.com/squall321/NewsKooo)"
# A realistic desktop-browser UA: the production crawler uses UA rotation /
# Playwright for bot-sensitive sites, so we retry 403/406/empty with this to
# measure what ingestion can *actually* fetch (not just what a bare bot gets).
_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


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
    via_browser: bool = False


def _evaluate(method: str, resp: httpx.Response) -> tuple[bool, int, str]:
    if resp.status_code >= 400:
        return False, 0, f"http {resp.status_code}"
    if method == "rss":
        n = len(feedparser.parse(resp.content).entries)
        return n > 0, n, ("ok" if n > 0 else "0 entries / unparseable")
    return True, 0, "reachable"


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

    # Pass 1 — bare bot UA (the conservative floor).
    status: int | None = None
    bot_err: str | None = None
    async with sem:
        try:
            resp = await client.get(target, headers={"User-Agent": _BOT_UA})
            ok, n, reason = _evaluate(method, resp)
            if ok:
                return Probe(name, region, method, target, resp.status_code, True, n, reason)
            status = resp.status_code
        except Exception as exc:  # report, never crash the sweep
            bot_err = f"error: {type(exc).__name__}"

    # Pass 2 — browser UA fallback (recovers 403/406/empty/transport blocks).
    async with sem:
        try:
            resp = await client.get(target, headers={"User-Agent": _BROWSER_UA})
        except Exception as exc:
            return Probe(name, region, method, target, status, False, 0, bot_err or f"error: {type(exc).__name__}")
    ok, n, reason = _evaluate(method, resp)
    if ok:
        return Probe(name, region, method, target, resp.status_code, True, n, f"{reason} (browser UA)", via_browser=True)
    return Probe(name, region, method, target, resp.status_code, False, n, reason)


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
    via_browser = sum(1 for p in probes if p.ok and p.via_browser)
    rss = [p for p in probes if p.fetch_method == "rss"]
    rss_ok = [p for p in rss if p.ok]
    broken = [p for p in rss if not p.ok]
    regions_ok = len({p.region for p in probes if p.ok})

    print("\n================ NewsKoo source coverage ================")
    print(f"sources probed   : {total}")
    print(f"reachable/usable : {ok}  ({ok * 100 // max(total, 1)}%)")
    print(f"  ...of which needed a browser UA (bot-walled): {via_browser}")
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
        "ok_via_browser_ua": via_browser,
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
