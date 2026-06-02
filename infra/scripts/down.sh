#!/usr/bin/env bash
# Stop the NewsKoo worker fleet + API started by `up.sh WORKERS=1`.
#   bash infra/scripts/down.sh         # stop workers + API
#   bash infra/scripts/down.sh --all   # also stop Postgres/Redis/Kafka
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
RUNDIR="${RUNDIR:-/var/run/newskoo}"

step() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }

step "stop workers + API"
if compgen -G "$RUNDIR/*.pid" >/dev/null; then
  for f in "$RUNDIR"/*.pid; do
    pid="$(cat "$f" 2>/dev/null || true)"
    name="$(basename "$f" .pid)"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null && echo "   stopped $name (pid $pid)"
    fi
    $SUDO rm -f "$f"
  done
else
  echo "   no pidfiles in $RUNDIR (nothing to stop)"
fi

if [ "${1:-}" = "--all" ]; then
  step "stop services (Postgres/Redis/Kafka)"
  $SUDO bash infra/scripts/dev-services.sh down || true
fi

printf '\n\033[1;32mNewsKoo stopped.\033[0m\n'
