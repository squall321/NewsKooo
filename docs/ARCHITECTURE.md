# NewsKoo — Architecture

## 1. Overview

NewsKoo is a distributed, event-driven pipeline that turns the world's public news into structured, queryable, LLM-reasoned intelligence. It is designed to scale horizontally (Kafka-decoupled stages) while running comfortably on a single powerful node for early operation.

```
                          ┌─────────────────────────────────────────────────────────┐
                          │                     SOURCE REGISTRY                       │
                          │  worldwide catalog: RSS · APIs · HTML · niche/scientific  │
                          │  per-source: region, language, method, politeness policy  │
                          └───────────────┬─────────────────────────────────────────-┘
                                          │ schedules
        ┌─────────────────────────────────┼─────────────────────────────────┐
        ▼                                 ▼                                 ▼
┌───────────────┐                ┌───────────────┐                ┌───────────────┐
│ RSS/Feed       │               │ API connectors │               │ HTML crawlers  │
│ collectors     │               │ GDELT, NewsAPI │               │ httpx + PW     │
│                │               │ official feeds │               │ politeness/    │
│                │               │                │               │ rotation/robots│
└──────┬─────────┘               └──────┬─────────┘               └──────┬────────-┘
       │                                │                                │
       └────────────────┬───────────────┴────────────────┬──────────────-┘
                        ▼  Kafka: raw.documents           │
                 ┌──────────────┐                         │
                 │  PARSE/EXTRACT│  trafilatura/selectolax │
                 │  + lang detect│  + C++ normalize        │
                 └──────┬────────┘                         │
                        ▼  Kafka: parsed.articles          │
                 ┌──────────────┐                          │
                 │ DEDUP/CLUSTER │  C++ simhash + embeddings│
                 │  → events     │  (pgvector similarity)   │
                 └──────┬────────┘                          │
                        ▼                                   │
                 ┌──────────────┐         ┌─────────────────▼────────────┐
                 │ POSTGRESQL    │◄────────│  ANALYZE (multi-LLM)         │
                 │ structured DB │         │  entities·keywords·sentiment │
                 │ pgvector+FTS  │────────►│  multilingual·summaries      │
                 └──────┬────────┘         └─────────────┬────────────────┘
                        │                                ▼
                        │                     ┌────────────────────────┐
                        │                     │ ISSUE DETECTION ENGINE │
                        │                     │ volume/velocity anomaly│
                        │                     │ → alerts               │
                        │                     └───────────┬────────────┘
                        ▼                                  ▼
              ┌──────────────────┐              ┌────────────────────┐
              │ FASTAPI           │              │ REPORT GENERATION   │
              │ query·search·SSE  │◄────────────►│ LLM cited reports   │
              └────────┬──────────┘              └────────────────────┘
                       ▼
              ┌──────────────────┐
              │ REACT FRONTEND    │
              │ dashboard·trends  │
              │ alerts·reports    │
              └──────────────────┘
```

## 2. Pipeline stages (Kafka topics)

| Topic | Producer | Consumer | Payload |
|-------|----------|----------|---------|
| `raw.documents` | RSS/API/HTML collectors | Parser | url, source_id, raw_html/raw_text, fetched_at, http_meta |
| `parsed.articles` | Parser | Dedup/Cluster + Persist | title, body, lang, published_at, authors, canonical_url |
| `dedup.events` | Dedup/Cluster | Persist + Analyze | article_id, event_id, simhash, near-dups |
| `analyze.requests` | Persist | Analyzer | article_id / event_id, requested analyses |
| `analyze.results` | Analyzer | Persist | entities, keywords, topics, sentiment, summary, embedding |
| `issues.alerts` | Issue engine | API/Notifier | topic/entity, score, window, supporting article_ids |

Stage decoupling means crawlers can burst, parsing can lag, and analysis (the expensive LLM stage) can backpressure independently. Each stage is a horizontally scalable consumer group.

## 3. Components

### 3.1 Source Registry & Discovery
- A catalog (`sources` table) describing every source: feed/API/HTML, region, language(s), category, bot-sensitivity, politeness policy, and health metrics.
- **Discovery agent**: RSS autodiscovery from homepages, sitemap parsing, OPML import, and curated seed lists — including scientific (arXiv, journals, EurekAlert, university press) and long-tail/niche feeds.
- Seeded with hundreds of worldwide sources across regions and languages.

### 3.2 Ingestion
- **RSS/Feed collectors** — cheapest, broadest coverage; most outlets expose feeds.
- **API connectors** — GDELT (global, free, massive), NewsAPI, and official publisher APIs.
- **HTML crawlers** — `httpx` + `selectolax` for static pages; **Playwright** for JS-heavy or bot-sensitive sites.
- **Politeness engine** — per-domain token-bucket rate limits (Redis), randomized delays, user-agent rotation, optional proxy pool, `robots.txt` parsing, and **round-robin across many domains** so no single site sees bursty traffic.

### 3.3 Parse / Extract
- Boilerplate-free article extraction (`trafilatura`), canonical URL + published date + authors.
- Language detection (fastText/langdetect) — original language preserved.
- **C++ accel**: Unicode-aware normalization and fast tokenization on the hot path.

### 3.4 Dedup / Cluster → Events
- **C++ simhash/minhash** for near-duplicate detection at scale; Redis bloom for seen-URL/hash gating.
- Cross-source / cross-language clustering into **events** using embedding similarity (pgvector). One real-world story = one event with many articles.

### 3.5 Analyze (multi-provider LLM)
- Provider-abstraction interface (`LLMProvider`) with Claude / OpenAI / local backends selected by config; prompt caching where supported.
- Extraction: named entities, keywords, topics/taxonomy, sentiment, and concise summaries — operating directly on original-language text.
- Embeddings stored in `pgvector` for semantic search and clustering.

### 3.6 Issue Detection Engine
- Time-series of entity/topic mention volume and **velocity** (acceleration of mentions).
- Anomaly detection (z-score / EWMA / burst detection) flags emerging issues early; emits `issues.alerts`.
- C++ for fast windowed aggregation across large article volumes.

### 3.7 Report Generation
- On-demand and scheduled reports keyed by user queries (keywords, sectors, products, regions).
- LLM synthesizes a cited report from the relevant events/articles; reports persisted and versioned.

### 3.8 API (FastAPI)
- REST for query/search/sources/reports; **SSE/WebSocket** for live alerts and ingestion stats.
- Async end-to-end (asyncpg, aiokafka).

### 3.9 Frontend (React + TS + Vite)
- Dashboard (ingestion health, volume trends), search (FTS + semantic), trend & velocity charts, issue alert feed, report viewer, and source management.
- shadcn/ui + Tailwind, TanStack Query/Table, Recharts/visx, Zustand.

## 4. Cross-cutting

- **Config**: Pydantic-settings, 12-factor env vars; one config schema shared across services.
- **Observability**: structured logging (structlog), Prometheus metrics, health endpoints.
- **Resilience**: idempotent consumers (upsert on canonical_url + content hash), dead-letter topics, retry with backoff.
- **Security**: secrets via env; API auth (API keys/JWT); no PII storage beyond public bylines.

## 5. Deployment

- **Dev**: WSL Ubuntu 20.04 — services run natively via `infra/scripts/dev-services.sh`.
- **Prod**: Ubuntu 22.04 — each component built as an **Apptainer** image (`infra/apptainer/*.def`) and run as Apptainer instances managed by scripts/systemd. Stateful services (PostgreSQL, Kafka, Redis) run as Apptainer instances with bound host volumes.
- Cross-platform contract: everything targets Linux; Windows participation is via WSL only.

See [DATA_MODEL.md](DATA_MODEL.md) for the schema and [ROADMAP.md](ROADMAP.md) for the build plan.
