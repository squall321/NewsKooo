# NewsKoo — Live Integration (run on Linux)

The full stack is implemented and unit-verified (ruff clean, ~180 mocked tests
green; frontend build green). **Live integration must run on Linux** (Ubuntu
20.04/22.04) — the dev box's WSL is currently unusable, and PostgreSQL/Kafka/the
C++ build all target Linux. This is the ordered checklist to take it live.

## TL;DR — one command

```bash
git clone https://github.com/squall321/NewsKooo && cd NewsKooo   # repo dir is "NewsKooo"
bash infra/scripts/live-integration.sh            # bring up + migrate + seed + smoke + tests
LIVE_RSS=1 bash infra/scripts/live-integration.sh # also fetch+parse a real feed
```
That script runs steps 1–7 below and prints `ALL GREEN` or the first failure.

---

## Ordered remaining work

### 1. Infrastructure up ✅ scripted
`infra/scripts/dev-services.sh install && up` — PostgreSQL 16 + `pgvector`,
Redis, Kafka (KRaft). (For hardened/multi-node prod use Apptainer instead, see
[OPERATIONS.md](OPERATIONS.md).)

### 2. Build + deps ✅ scripted
`cd backend && uv sync --extra native --extra llm --group dev` — installs deps
and **builds the C++ `newskoo_native`** module (g++ + cmake≥3.15). Confirm
`python -c "import newskoo_native"`.

### 3. Schema ✅ scripted
`uv run alembic upgrade head` — applies the hand-written baseline (extensions
`vector`/`pg_trgm`, all tables, **HNSW** vector indexes, generated `tsv` FTS).
First true test of the schema against a real Postgres.

### 4. Kafka topics + seed ✅ scripted
`uv run python -m newskoo.core.topics` then `uv run python -m newskoo.sources.seed_cli`
(seeds the 274-source worldwide catalog; idempotent).

### 5. Smoke ✅ scripted
`uv run python -m newskoo.smoke [--live-rss]` — DB roundtrip + FTS + pgvector
cosine query; `--live-rss` also fetches/parses/persists a real feed entry.

### 6. LLM enablement ⏳ needs secrets
Set in `.env` (copy from `.env.example`): `NEWSKOO_LLM_PROVIDER` +
`NEWSKOO_ANTHROPIC_API_KEY` **or** `NEWSKOO_OPENAI_API_KEY`, and an embedding
backend (`NEWSKOO_EMBEDDING_PROVIDER=openai` with a key, or `local` with Ollama
at `NEWSKOO_OLLAMA_BASE_URL`). Then validate live:
- `analyzer` worker turns `analyze.requests` → `analyze.results` (entities/
  keywords/topics/sentiment/summary + embedding).
- report generation: `POST /api/reports` returns a cited report.
Embeddings must match `NEWSKOO_EMBEDDING_DIM` (default 1024 = the pgvector
column width); change both together if you switch models.

### 7. Worker fleet (Kafka E2E) ⏳ ops
Start the stages and confirm a document flows end-to-end:
```bash
for s in ingest parser persist results analyzer issues; do
  uv run python -m newskoo.workers.run "$s" &   # prod: systemd units, infra/systemd/
done
```
Expected flow: `raw.documents → parsed.articles → DB + analyze.requests →
analyze.results → DB + clustering → issues.alerts`. Watch consumer lag.

### 8. Crawl tuning ⏳ ops
Enable a subset of sources first; watch `crawl_log` + each source's `health`
jsonb; adjust `politeness` per source. Respect robots/ToS. For JS/bot-sensitive
sites install Playwright: `uv run playwright install --with-deps chromium`
(optional `browser` extra).

### 9. API + frontend ⏳ ops
- API: `uv run uvicorn newskoo.api.main:app --host 0.0.0.0 --port 8000`; check
  `/health`, `/api/sources`, `/api/search`, `/api/trends`, `/metrics`.
- Frontend: set `VITE_API_BASE`, `npm run build`, serve `dist/` (or
  `apptainer run frontend.sif`) behind nginx/caddy with TLS.
- Set `NEWSKOO_API_KEY` to require auth on mutations.

### 10. Scale & monitor ⏳ ops
Prometheus scrape (`infra/monitoring/prometheus.yml`) → Grafana. Scale the
`analyzer` stage (LLM-bound) independently; raise Kafka partitions for
throughput. When volume grows, add time-range **partitioning** of
`articles`/`crawl_log` (a follow-up Alembic ops migration; ORM already designed
for it — see `models/base.py`).

---

## Known constraints / notes
- **No live LLM test without keys.** Steps 1–5,7(non-LLM),8,9 work without any
  API key; step 6 and report generation need a provider configured.
- **C++ parity.** `newskoo_native` and the pure-Python fallback in
  `core/accel.py` use the same simhash/normalize semantics; dedup is consistent
  whether or not the extension is built. ICU-grade Unicode normalization is a
  possible future hardening.
- **Prod packaging.** `infra/apptainer/*.def` + `infra/systemd/*` +
  `infra/scripts/prod-services.sh` cover the Apptainer/systemd deployment;
  [OPERATIONS.md](OPERATIONS.md) is the runbook.
