# NewsKoo — Source Coverage (empirical)

How many sites can we actually see? This is the **measured** answer, not the
seed count. Reproduce any time:

```bash
cd backend && uv run python -m newskoo.sources.validate --json coverage.json
```

The validator (`newskoo/sources/validate.py`) probes every seeded source
concurrently over the live web: RSS feeds are fetched **and parsed** (counts
real entries), HTML sources get a reachability check, and `api` sources are
classified (GDELT is keyless/always-on; NewsAPI is key-gated). It needs network
but no DB.

## Snapshot — 2026-05-31 (single bot UA, no Playwright)

| metric | value |
|--------|------:|
| sources probed | **274** |
| reachable / usable | **203 (74%)** |
| distinct regions reachable | **52** |
| live RSS feeds (≥1 entry) | **199 / 265** |
| **article entries seen in this one snapshot** | **~8,100** |
| api (GDELT keyless) | 3 / 4 |
| html homepages reachable | 1 / 5 |

So in a single pass NewsKoo already pulls **~8,100 articles from ~199 feeds
across 52 regions** — and that excludes GDELT, which by itself monitors
100k+ outlets worldwide and is reachable.

## Caveats (why this is a *floor*, not a ceiling)
- The probe uses **one bot user-agent and no Playwright**, so every `403` below
  is *pessimistic*: the production ingestion layer rotates user-agents and falls
  back to a real browser (Playwright) for bot-sensitive sites, recovering many of
  them. A `403` here usually means "the URL is fine, the bare bot was blocked".
- A snapshot counts entries *currently* in each feed; throughput over time is far
  higher (feeds refresh continuously).
- GDELT/NewsAPI connectors multiply reach well beyond the curated direct feeds.

## Broken feeds (66) — categories
- **403 bot-block (~24):** URL likely valid; recovered in prod via UA rotation /
  Playwright (bump `bot_sensitivity`). e.g. Politico, Les Échos, MIT/Stanford/
  Cambridge news, OECD, IEA, Times of Israel, Haaretz, Al Arabiya, Inquirer.
- **404 moved (~21):** feed path changed → needs the current URL. e.g. Globe and
  Mail, Nature, EurekAlert, Scientific American, NHK World, Caixin, Gulf News,
  Oxford, Max Planck, CERN, BIS.
- **arXiv format change (8):** `export.arxiv.org/rss/*` now returns an empty/new
  format → use `https://rss.arxiv.org/rss/<cat>`.
- **0-entries / unparseable (~5):** USA Today, Korea Herald, IMF, World Bank,
  AnandTech — wrong endpoint/format.
- **timeouts / connect errors (~6):** Reuters (public RSS discontinued), TASS,
  CBC, Financial Post, Emol, Swissinfo (410) — transient, geo, or retired.

Repairs (corrected URLs, bot_sensitivity bumps, html fallbacks) are tracked in
the seed catalog; re-run the validator to see the updated number.
