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

## Snapshot (single bot UA, no Playwright — a conservative floor)

| metric | initial bot-UA | repaired bot-UA | **repaired + browser-UA fallback** |
|--------|------:|------:|------:|
| sources probed | 274 | 274 | **274** |
| reachable / usable | 203 (74%) | 235 (85%) | **241 (88%)** |
| distinct regions reachable | 52 | 57 | **58** |
| live RSS feeds (≥1 entry) | 199 / 265 | 220 / 251 | **226 / 251** |
| **article entries seen in one snapshot** | ~8,100 | ~11,051 | **~13,111** |
| api (GDELT keyless) | 3 / 4 | 3 / 4 | 3 / 4 |
| html reachable | 1 / 5 | 12 / 19 | 12 / 19 |

So in a single pass NewsKoo now pulls **~13,000 articles from ~226 feeds across
58 regions** — excluding GDELT, which alone monitors 100k+ outlets worldwide and
is reachable. The validator does a two-pass probe: a bare-bot UA, then a
**browser-UA fallback** on 403/406/empty (mirroring how ingestion escalates).
The repair round lifted usable sources 203 → 235; the browser-UA pass adds a few
more → **241 (88%)**. Only ~4 sites were recovered by the UA swap alone — the
remaining ~17 red feeds are hard anti-bot walls (Cloudflare / Akamai JS
challenges) that need **full Playwright** (headless JS execution), which the
production ingestion layer has but this probe does not run.

## Caveats (why this is a *floor*, not a ceiling)
- The probe uses **one bot user-agent and no Playwright**, so every `403` below
  is *pessimistic*: the production ingestion layer rotates user-agents and falls
  back to a real browser (Playwright) for bot-sensitive sites, recovering many of
  them. A `403` here usually means "the URL is fine, the bare bot was blocked".
- A snapshot counts entries *currently* in each feed; throughput over time is far
  higher (feeds refresh continuously).
- GDELT/NewsAPI connectors multiply reach well beyond the curated direct feeds.

## Broken feeds — initial probe (66) and what was done
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

**Repairs applied** (in `seeds.py` `_CORRECTIONS`, verified by re-probe): ~23
corrected feed URLs (Arc-platform feeds, arXiv → `rss.arxiv.org`, moved paths
like BIS/Oxford/CERN/Jakarta Post/Korea Herald), ~21 `bot_sensitivity` bumps for
403 bot-walls (URL kept; production recovers via UA rotation / Playwright), and
~13 html fallbacks for retired feeds (Reuters, USA Today, Gulf News, EurekAlert,
IMF, World Bank, AnandTech, …). Result: 203 → **235 usable**, 8,100 → **11,051
entries**. The ~39 still red to the bare-bot probe are predominantly the
bot-walled 403s, which the live ingestion stack is built to fetch. Re-run
`python -m newskoo.sources.validate` any time to refresh these numbers.
