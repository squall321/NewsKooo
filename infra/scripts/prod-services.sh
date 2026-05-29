#!/usr/bin/env bash
# Production orchestration on Ubuntu 22.04 with Apptainer.
#
#   build      build backend.sif + frontend.sif
#   infra-up   start PostgreSQL(pgvector) + Redis + Kafka as Apptainer instances
#   infra-down stop those instances
#   migrate    run alembic migrations + create Kafka topics
#   status     show running instances
#
# Stateful services run as rootless Apptainer instances with host-bound volumes.
# NOTE: rootless Postgres/Kafka need a writable data bind and env passed via
# APPTAINERENV_*. For a hardened setup you may prefer host-native packages under
# systemd (mirrors infra/scripts/dev-services.sh) — both are supported; see
# docs/OPERATIONS.md.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SIF_DIR="${SIF_DIR:-/opt/newskoo}"
DATA="${NEWSKOO_DATA:-/srv/newskoo}"
ENV_FILE="${ENV_FILE:-/etc/newskoo.env}"

log() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }

cmd_build() {
  log "Build backend.sif"
  apptainer build "${SIF_DIR}/backend.sif" "${ROOT}/infra/apptainer/backend.def"
  log "Build frontend.sif"
  apptainer build "${SIF_DIR}/frontend.sif" "${ROOT}/infra/apptainer/frontend.def"
}

cmd_infra_up() {
  mkdir -p "${DATA}/pg" "${DATA}/redis" "${DATA}/kafka"

  log "PostgreSQL (pgvector) instance"
  APPTAINERENV_POSTGRES_PASSWORD=newskoo \
  APPTAINERENV_POSTGRES_USER=newskoo \
  APPTAINERENV_POSTGRES_DB=newskoo \
  APPTAINERENV_PGDATA=/var/lib/postgresql/data/pgdata \
  apptainer instance start \
    --bind "${DATA}/pg:/var/lib/postgresql/data" \
    docker://pgvector/pgvector:pg16 newskoo-pg
  apptainer run instance://newskoo-pg postgres >/dev/null 2>&1 &

  log "Redis instance"
  apptainer instance start --bind "${DATA}/redis:/data" docker://redis:7 newskoo-redis
  apptainer run instance://newskoo-redis redis-server --dir /data >/dev/null 2>&1 &

  log "Kafka (KRaft) instance"
  APPTAINERENV_KAFKA_NODE_ID=1 \
  APPTAINERENV_KAFKA_PROCESS_ROLES=broker,controller \
  APPTAINERENV_KAFKA_CONTROLLER_QUORUM_VOTERS=1@localhost:9093 \
  APPTAINERENV_KAFKA_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093 \
  APPTAINERENV_KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  APPTAINERENV_KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER \
  apptainer instance start --bind "${DATA}/kafka:/var/lib/kafka/data" \
    docker://apache/kafka:3.8.1 newskoo-kafka
  log "infra-up issued (give Kafka ~15s to elect)."
}

cmd_infra_down() {
  for inst in newskoo-kafka newskoo-redis newskoo-pg; do
    apptainer instance stop "$inst" 2>/dev/null || true
  done
}

cmd_migrate() {
  log "Alembic upgrade head"
  apptainer exec --env-file "${ENV_FILE}" "${SIF_DIR}/backend.sif" \
    bash -lc 'cd /opt/newskoo/backend && uv run alembic upgrade head'
  log "Create Kafka topics"
  apptainer exec --env-file "${ENV_FILE}" "${SIF_DIR}/backend.sif" \
    bash -lc 'cd /opt/newskoo/backend && uv run python -m newskoo.core.topics'
}

cmd_status() { apptainer instance list; }

case "${1:-}" in
  build)      cmd_build ;;
  infra-up)   cmd_infra_up ;;
  infra-down) cmd_infra_down ;;
  migrate)    cmd_migrate ;;
  status)     cmd_status ;;
  *) echo "usage: $0 {build|infra-up|infra-down|migrate|status}"; exit 2 ;;
esac
