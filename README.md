# NewsKoo

> Global news intelligence platform — crawl the world's news, store it structured for LLM reasoning, and surface emerging issues fast.

NewsKoo ingests news from **anywhere** (RSS, official APIs, GDELT, and polite HTML crawling), stores **title + body only** (no images) in a structured PostgreSQL schema optimized for LLM context retrieval, deduplicates and clusters articles into **events** across sources and languages, and runs **multi-provider LLM analysis** to detect trending topics, products, economic signals, and emerging issues — across every domain, including niche and scientific topics. Ultimately a signal source for use cases like equities research.

## Core goals

- **Boundary-less coverage** — economy, products, tech, science, and long-tail/minor topics worldwide.
- **Multilingual by design** — store original-language text; the LLM layer reasons across languages directly.
- **Issue detection** — spot what's becoming a story before it's obvious, via volume/velocity anomaly detection on topics and entities.
- **Structured for reasoning** — sources → articles → entities/keywords → events → reports, with full-text + vector search.
- **Polite & resilient crawling** — per-domain rate limits, rotation across many sites, robots awareness, and API-first where available.
- **Fast where it counts** — C++ (pybind11) accelerates dedup/simhash, text normalization, and hot aggregation paths.

## Stack

| Layer | Choice |
|-------|--------|
| Backend | Python 3.13 (managed by `uv`), FastAPI, SQLAlchemy 2.0 + Alembic, asyncpg, Pydantic v2 |
| Messaging | Apache Kafka (KRaft mode) via `aiokafka` |
| Storage | PostgreSQL 16 + `pgvector` + full-text search; partitioned by time |
| Cache / rate-limit | Redis |
| Performance | C++17 via `pybind11` + CMake (dedup, normalization, aggregation) |
| Crawling | `httpx` + `selectolax`/`trafilatura`; Playwright for JS-heavy / bot-sensitive sites |
| LLM | Provider-abstraction layer (Claude / OpenAI / local), original-language input |
| Frontend | React 18 + TypeScript + Vite, Tailwind + shadcn/ui, TanStack Query, Recharts |
| Dev env | **WSL** (Ubuntu 20.04) |
| Prod | **Linux (Ubuntu 22.04)** packaged as **Apptainer** containers |

## Repository layout

```
NewsKoo/
├── docs/            Architecture, roadmap, data model, decisions (START HERE)
├── backend/         FastAPI app, ingestion, parsing, analysis, workers (Python/uv)
├── native/          C++ acceleration modules (pybind11 + CMake)
├── frontend/        React + TS + Vite UI
├── infra/
│   ├── apptainer/   .def files for prod containers
│   ├── scripts/     dev bootstrap + service management
│   └── sql/         DB init / extensions
└── .github/         CI workflows
```

## Quick start (WSL)

```bash
# 1. Bootstrap the dev toolchain (build tools, uv+Python 3.13, Node 22)
bash infra/scripts/dev-bootstrap.sh

# 2. Bring up dev services (PostgreSQL, Redis, Kafka)
bash infra/scripts/dev-services.sh up

# 3. Backend
cd backend && uv sync && uv run alembic upgrade head
uv run uvicorn newskoo.api.main:app --reload

# 4. Frontend
cd frontend && npm install && npm run dev
```

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system design, data flow, components
- [docs/ROADMAP.md](docs/ROADMAP.md) — phased build plan (Phase 0–10)
- [docs/DATA_MODEL.md](docs/DATA_MODEL.md) — PostgreSQL schema for LLM-friendly storage
- [docs/DECISIONS.md](docs/DECISIONS.md) — architecture decision records

## Legal & ethics

NewsKoo crawls public news content for analysis. It respects `robots.txt`, applies conservative per-domain rate limits, prefers official APIs and RSS, and stores only text (title + body) with source attribution. Operators are responsible for complying with each source's Terms of Service and applicable copyright/database law in their jurisdiction.
