# NewsKoo — Build Roadmap

Phased plan. Each phase has a clear deliverable and is built largely in parallel by sub-agents. Phases 1–10 each land working, tested code behind a Kafka/DB contract so stages integrate cleanly.

Legend: 🟢 done · 🟡 in progress · ⚪ pending

---

## Phase 0 — Foundation ⚪
**Goal:** repo skeleton everyone builds on.
- Monorepo layout (`backend/ native/ frontend/ infra/ docs/`).
- `uv` Python project, ruff/black/mypy config, pytest.
- C++ CMake + pybind11 skeleton.
- Vite + React + TS skeleton with Tailwind/shadcn.
- Shared config schema (Pydantic-settings), structured logging.
- `LLMProvider` abstraction interface (no impl yet).
- CI skeleton (.github/workflows), `.gitignore`, docs.
- Git init → connect to `github.com/squall321/NewsKooo` → first push.

## Phase 1 — Data model & infra ⚪
**Goal:** the structured backbone.
- PostgreSQL schema: `sources, articles, article_versions, entities, article_entities, keywords, topics, events, event_articles, analysis, reports, crawl_log`.
- `pgvector` embeddings, `tsvector` full-text, **time-based partitioning** on `articles`.
- Alembic baseline migration + seed extensions (`pgvector`, `pg_trgm`).
- Kafka topic definitions + `aiokafka` producer/consumer helpers (KRaft).
- Redis helpers (rate-limit token bucket, seen-set/bloom).
- `infra/scripts/dev-services.sh` (Postgres/Redis/Kafka up/down in WSL).
- `infra/apptainer/*.def` baseline for prod.

## Phase 2 — Source registry & discovery ⚪
**Goal:** know where the news is — everywhere.
- Source registry CRUD + health tracking.
- Seed catalog: hundreds of worldwide sources across regions/languages, incl. **scientific** (arXiv, EurekAlert, Nature/Science feeds, university PR) and **niche/long-tail**.
- Discovery: RSS autodiscovery, sitemap & OPML import, GDELT source expansion.
- GDELT + NewsAPI + generic RSS connector contracts.

## Phase 3 — Ingestion ⚪
**Goal:** pull data at scale, politely.
- RSS/feed collector → `raw.documents`.
- API connectors (GDELT, NewsAPI) → `raw.documents`.
- HTML crawler: `httpx`+`selectolax` static, Playwright for JS/bot-sensitive.
- Politeness engine: per-domain token bucket (Redis), UA rotation, proxy hook, robots.txt, **round-robin domain scheduling**.
- Crawl scheduler (APScheduler) honoring per-source cadence.

## Phase 4 — Parse / extract + C++ accel ⚪
**Goal:** clean text, fast.
- Article extraction (title/body/date/authors/canonical), language detection.
- C++ module (pybind11): Unicode normalization, fast tokenization, **simhash** dedup.
- Consume `raw.documents` → produce `parsed.articles`.

## Phase 5 — Storage & clustering ⚪
**Goal:** persist and connect.
- Idempotent persistence (upsert by canonical_url + content hash).
- Near-dup gating (simhash + Redis), event clustering across sources/languages via embeddings.
- Embedding generation pipeline → pgvector.

## Phase 6 — Analysis & issue detection ⚪
**Goal:** meaning and signals.
- Multi-provider LLM impls (Claude/OpenAI/local) behind `LLMProvider`.
- Entity/keyword/topic/sentiment extraction + summaries (multilingual input).
- Issue detection engine: volume/velocity anomaly detection → `issues.alerts`.

## Phase 7 — FastAPI backend ⚪
**Goal:** expose everything.
- Routers: `/sources /articles /events /search /trends /issues /reports`.
- FTS + semantic (pgvector) search; trend/velocity aggregation endpoints.
- SSE/WebSocket for live alerts & ingestion stats; auth (API key/JWT).

## Phase 8 — Frontend ⚪
**Goal:** the most modern UI.
- Dashboard, search, trend/velocity charts, issue alert feed, report viewer, source admin.
- shadcn/ui + Tailwind, TanStack Query/Table, Recharts, Zustand.

## Phase 9 — Report generation ⚪
**Goal:** publishable intelligence.
- Query-driven (keywords/sector/product/region) cited LLM reports.
- Scheduled report jobs; versioned report storage; export (MD/PDF).

## Phase 10 — Ops & deployment ⚪
**Goal:** run it on Linux for real.
- Apptainer images for every component + orchestration/start-stop scripts + systemd units.
- CI/CD (build, test, image publish), Prometheus/Grafana, runbooks, scaling guide.

---

## Dependency graph
```
P0 → P1 → P2 → P3 → P4 → P5 → P6 → P7 → P8
                                  └→ P9 (uses P6)
P10 spans all (packaging) and lands last.
```

## Parallelization strategy
- Within a phase, sub-agents own non-overlapping modules/files (no write conflicts).
- Cross-stage contracts (Kafka payloads, DB schema, `LLMProvider`) are frozen in P0/P1 so later stages build independently against stable interfaces.
