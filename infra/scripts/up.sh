#!/usr/bin/env bash
# Turnkey bring-up on Linux (Ubuntu 20.04/22.04): one command takes a fresh box
# to a running NewsKoo — services up + healthy, deps built, schema migrated,
# topics created, catalog seeded, and (optionally) the worker fleet + API live.
#
#   bash infra/scripts/up.sh                 # infra + migrate + seed (no workers)
#   WORKERS=1 bash infra/scripts/up.sh        # + start the worker fleet + API
#   SKIP_INSTALL=1 bash infra/scripts/up.sh   # skip apt install (already installed)
#
# Idempotent: safe to re-run. Waits for Postgres/Redis/Kafka to be healthy
# before migrating. Needs outbound network for the first run (apt + uv).
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
export PATH="$HOME/.local/bin:$PATH"
WORKERS="${WORKERS:-0}"
SKIP_INSTALL="${SKIP_INSTALL:-0}"
RUNDIR="${RUNDIR:-/var/run/newskoo}"; LOGDIR="${LOGDIR:-/var/log/newskoo}"

step() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m[FATAL]\033[0m %s\n' "$*"; exit 1; }

wait_for() {  # wait_for <label> <max_secs> <cmd...>
  local label="$1" max="$2"; shift 2
  printf '   waiting for %s' "$label"
  for _ in $(seq 1 "$max"); do
    if "$@" >/dev/null 2>&1; then printf ' ok\n'; return 0; fi
    printf '.'; sleep 1
  done
  printf ' TIMEOUT\n'; return 1
}

command -v uv >/dev/null 2>&1 || { step "install uv"; curl -LsSf https://astral.sh/uv/install.sh | sh; export PATH="$HOME/.local/bin:$PATH"; }

step "0/7 .env bootstrap"
[ -f .env ] || { cp .env.example .env; echo "   created .env from .env.example — edit secrets (LLM keys) before analysis."; }

step "1/7 install + start services (Postgres+pgvector, Redis, Kafka)"
[ "$SKIP_INSTALL" = "1" ] || $SUDO bash infra/scripts/dev-services.sh install
$SUDO bash infra/scripts/dev-services.sh up

step "2/7 wait for service health"
wait_for postgres 60 bash -c 'PGPASSWORD=newskoo psql -h localhost -U newskoo -d newskoo -c "select 1"' || die "postgres not healthy"
wait_for redis 30 redis-cli ping || die "redis not healthy"
wait_for kafka 90 bash -c '/opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server localhost:9092' || die "kafka not healthy"

cd backend
step "3/7 sync backend (native C++ + llm + dev)"
uv sync --extra native --extra llm --group dev || die "uv sync failed"

step "4/7 migrate schema (alembic upgrade head)"
uv run alembic upgrade head || die "migration failed"

step "5/7 create Kafka topics"
uv run python -m newskoo.core.topics || die "topic creation failed"

step "6/7 seed catalog (sources + securities)"
uv run python -m newskoo.sources.seed_cli
uv run python -m newskoo.signals.cli seed || true

if [ "$WORKERS" = "1" ]; then
  step "7/7 start worker fleet + API"
  $SUDO mkdir -p "$RUNDIR" "$LOGDIR"
  for s in ingest parser persist results analyzer issues; do
    nohup uv run python -m newskoo.workers.run "$s" >"$LOGDIR/worker-$s.log" 2>&1 &
    echo "$!" | $SUDO tee "$RUNDIR/worker-$s.pid" >/dev/null
    echo "   started worker:$s (pid $!)"
  done
  nohup uv run uvicorn newskoo.api.main:app --host 0.0.0.0 --port "${NEWSKOO_API_PORT:-8000}" \
    >"$LOGDIR/api.log" 2>&1 &
  echo "$!" | $SUDO tee "$RUNDIR/api.pid" >/dev/null
  echo "   started api (pid $!) on :${NEWSKOO_API_PORT:-8000}"
  echo "   logs in $LOGDIR ; stop with: bash infra/scripts/down.sh"
else
  step "7/7 done (infra ready)"
  echo "   start workers + API with: WORKERS=1 bash infra/scripts/up.sh"
  echo "   or one-shot validation: bash infra/scripts/live-integration.sh"
fi

printf '\n\033[1;32m================ NewsKoo is up ================\033[0m\n'
echo "API health: curl -s localhost:${NEWSKOO_API_PORT:-8000}/health"
