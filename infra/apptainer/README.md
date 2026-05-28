# Apptainer (production)

Production runs on Ubuntu 22.04 with each component as an Apptainer image.
Dev uses native WSL services (`infra/scripts/dev-services.sh`); these `.def`
files are the **prod** artifacts.

## Images
- `backend.def` — FastAPI API + Kafka workers + native C++ accel (one image, multiple run modes).
- `frontend.def` *(Phase 10)* — builds the Vite app and serves static via a tiny server / or copy `dist/` to a reverse proxy.

## Build
```bash
# from repo root, on the prod host (or CI):
apptainer build backend.sif infra/apptainer/backend.def
```

## Run
```bash
# API
apptainer run --env-file .env backend.sif api
# A worker stage (parser|dedup|analyzer|issues)
apptainer run --env-file .env backend.sif worker parser
```

## Stateful services (PostgreSQL, Kafka, Redis)
Two supported options on the prod host:
1. **Apptainer instances** with bound host volumes (rootless):
   ```bash
   apptainer instance start --bind /srv/newskoo/pg:/var/lib/postgresql docker://pgvector/pgvector:pg16 pg
   apptainer instance start docker://redis:7 redis
   apptainer instance start docker://apache/kafka:3.8.1 kafka
   ```
2. **Host-native** packages managed by systemd (mirrors `dev-services.sh`).

Orchestration scripts + systemd units land in Phase 10 (`infra/scripts/prod-*`).

> Note: `Bootstrap: docker` pulls base images via Apptainer's OCI support; no
> Docker daemon is required.
