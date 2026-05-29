# NewsKoo — Operations Runbook

Production target: **Ubuntu 22.04**, components packaged as **Apptainer** images.
Dev: **WSL Ubuntu 20.04** with native services. Everything targets Linux.

## Topology

```
            ┌── frontend.sif (serve dist :4173) ──┐
 reverse    │                                     │
 proxy/TLS ─┤── backend.sif api (:8000) ──────────┤── PostgreSQL 16 + pgvector
 (nginx/    │                                     │── Redis 7
  caddy)    └── backend.sif worker x{ingest,parser,│── Kafka 3.8 (KRaft)
                persist,results,analyzer,issues}   │
```

Stateful services (Postgres/Redis/Kafka) + the stateless app (api/workers).
Stages are decoupled over Kafka, so each worker stage scales independently as a
consumer group.

## 1. Host prep (Ubuntu 22.04)

```bash
# Apptainer
sudo add-apt-repository -y ppa:apptainer/ppa
sudo apt-get update && sudo apt-get install -y apptainer
# dedicated user + dirs
sudo useradd -r -m -d /srv/newskoo newskoo
sudo install -d -o newskoo -g newskoo /opt/newskoo /srv/newskoo
sudo cp .env.example /etc/newskoo.env   # then edit secrets (API keys, DSNs)
```

`/etc/newskoo.env` must set at least `NEWSKOO_POSTGRES_DSN`,
`NEWSKOO_KAFKA_BOOTSTRAP_SERVERS`, `NEWSKOO_REDIS_URL`, the LLM provider + key,
and (recommended) `NEWSKOO_API_KEY` to require auth on mutations.

## 2. Build images

```bash
SIF_DIR=/opt/newskoo bash infra/scripts/prod-services.sh build
# → /opt/newskoo/backend.sif, /opt/newskoo/frontend.sif
```

## 3. Bring up infrastructure

**Option A — Apptainer instances (single node):**
```bash
sudo bash infra/scripts/prod-services.sh infra-up    # pg + redis + kafka
sudo bash infra/scripts/prod-services.sh migrate     # alembic + Kafka topics
```
**Option B — host-native (hardened / multi-node):** install Postgres 16
(+`postgresql-16-pgvector`), Redis, and a Kafka cluster via your standard
config management, then run `migrate`. The dev script
`infra/scripts/dev-services.sh` is a working reference for the native install.

## 4. Run the app (systemd)

```bash
sudo cp infra/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now newskoo-api.service
for s in ingest parser persist results analyzer issues; do
  sudo systemctl enable --now "newskoo-worker@$s.service"
done
```
Frontend: `apptainer run --env VITE_API_BASE=https://api.example /opt/newskoo/frontend.sif`
behind nginx/caddy (TLS + SPA fallback). Or build `dist/` in CI and serve from the proxy directly.

## 5. Scaling

- **Throughput knob:** Kafka partitions (`NEWSKOO_KAFKA_NUM_PARTITIONS`, default 12).
- **Scale a stage:** run more `newskoo-worker@<stage>` instances (same consumer
  group rebalances partitions). The LLM `analyzer` stage is the usual bottleneck
  — scale it independently; crawl throughput is unaffected by analysis lag.
- **Politeness:** per-domain rate limits live in Redis; raising worker count does
  not increase per-domain request rate.

## 6. Monitoring

- API exposes Prometheus metrics at `/metrics`; scrape with
  `infra/monitoring/prometheus.yml`. Add node/kafka/postgres exporters as noted.
- Health: `GET /health`. Logs are structured (JSON when `NEWSKOO_LOG_JSON=true`).
- Key signals: Kafka consumer lag per stage, crawl error rate (from `crawl_log` /
  source `health`), LLM token spend (in `analysis.cost_usd`), DB connection pool.

## 7. Common tasks

- **Seed sources:** `apptainer exec ... backend.sif bash -lc 'cd /opt/newskoo/backend && uv run python -c "import asyncio; from newskoo.core.db import session_scope; from newskoo.sources import seed_sources; asyncio.run((lambda: (lambda s: None)(...))())"'` — or add a small CLI; `seed_sources(session)` is idempotent.
- **New migration:** `uv run alembic revision --autogenerate -m "..."` then `alembic upgrade head`.
- **Add Kafka topics / repartition:** `python -m newskoo.core.topics`.
- **Backups:** `pg_dump` the `newskoo` DB; Kafka is a transient bus (replayable from sources), not a system of record.

## 8. Disk note (dev)

Dev builds (uv venv, node_modules, caches) can be large — keep them off a full
data drive. On this dev box the repo lives on `D:` but the Python venv is created
on `C:` (`UV_PROJECT_ENVIRONMENT`), and the WSL distro itself lives at
`D:\wsl\Ubuntu_2004`. See README "Quick start".
