# NewsKoo — Architecture Decision Records

Short, dated records of the choices that shape the system. Newest first.

---

## ADR-0008 — Python 3.13 via `uv`
**Date:** 2026-05-29 · **Status:** accepted
Use the latest stable Python (3.13), managed by `uv`. WSL dev is Ubuntu 20.04 (system Python 3.8) and prod is 22.04 (3.10); `uv` installs/pins 3.13 uniformly so dev and prod match regardless of distro Python. Lockfile via `uv.lock`.

## ADR-0007 — Dev on WSL, prod on Linux 22.04 with Apptainer
**Date:** 2026-05-29 · **Status:** accepted
Development happens inside **WSL (Ubuntu 20.04)** — the whole project targets Linux; Windows participates only through WSL (no native-Windows path). Production runs on **Ubuntu 22.04** with each component packaged as an **Apptainer** (formerly Singularity) image. Apptainer chosen by operator preference (HPC-friendly, rootless, single-file `.sif`). Dev services run natively in WSL for speed; Apptainer `.def` files in `infra/apptainer/` are the prod artifact. Implication: avoid Docker-only assumptions; orchestration via scripts/systemd, not Compose.

## ADR-0006 — Kafka-based distributed architecture
**Date:** 2026-05-29 · **Status:** accepted
Stages (collect → parse → dedup → persist → analyze → detect) are decoupled by **Apache Kafka** (KRaft mode, no ZooKeeper). Enables independent horizontal scaling and backpressure — the expensive LLM stage can lag without dropping crawl throughput. Runs single-broker in dev, multi-broker in prod. `aiokafka` for async producers/consumers; consumer groups per stage.

## ADR-0005 — Original-language storage; LLM reasons multilingually
**Date:** 2026-05-29 · **Status:** accepted
Store article title/body in the **original language**; do not pre-translate on ingest. The analysis LLM handles multilingual content directly (entities, keywords, sentiment, cross-language clustering). Translations/summaries are produced on demand and stored as derived `analysis` rows. Saves bulk-translation cost and preserves fidelity; semantic cross-language linking is via multilingual embeddings.

## ADR-0004 — Multi-provider LLM abstraction
**Date:** 2026-05-29 · **Status:** accepted
All LLM access goes through an `LLMProvider` interface (chat/extract/embed) with interchangeable backends (Claude, OpenAI, local/Ollama) selected by config. Prompt caching used where supported. Avoids lock-in and lets cost/quality be tuned per task (cheap model for tagging, strong model for reports).

## ADR-0003 — C++ (pybind11) for performance-critical paths
**Date:** 2026-05-29 · **Status:** accepted
Hot paths — simhash/minhash dedup, Unicode normalization/tokenization, windowed mention aggregation — implemented in **C++17** exposed via **pybind11**, built with CMake. Python orchestrates; C++ does the per-document and per-window heavy lifting. Built in WSL/Linux (g++), shipped inside Apptainer images.

## ADR-0002 — PostgreSQL as the structured store
**Date:** 2026-05-29 · **Status:** accepted
Single source of truth is **PostgreSQL 16** with `pgvector` (semantic search/clustering) and native full-text (`tsvector`). Time-partitioned `articles`/`crawl_log`. Chosen over a document store because relationships (source→article→entity→event→report) and hybrid lexical+vector search are first-class and LLM-context retrieval is relationship-heavy. Redis is cache/rate-limit only, not a system of record.

## ADR-0001 — Boundary-less, polite, API-first ingestion
**Date:** 2026-05-29 · **Status:** accepted
Collect across **all domains and regions** including niche/scientific. Prefer **APIs and RSS** (cheap, ToS-friendly, high coverage) before HTML crawling. HTML crawling is **polite by default**: per-domain rate limits, round-robin across many domains, UA rotation, robots.txt awareness, Playwright only for JS/bot-sensitive sites. Store text only (title+body) with source attribution.

## ADR-0000 — Frontend: React + TypeScript + Vite
**Date:** 2026-05-29 · **Status:** accepted
Modern SPA with React 18 + TS + Vite, Tailwind + shadcn/ui, TanStack Query/Table, Recharts/visx, Zustand. FastAPI backend serves REST + SSE/WebSocket.
