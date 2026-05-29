#!/usr/bin/env bash
# One-shot LIVE integration on a Linux box (Ubuntu 20.04/22.04).
# Brings up real services, builds everything, migrates, seeds, and runs an
# end-to-end smoke + the full test suite. Designed to be the single command you
# run on the target Linux machine to validate the whole stack.
#
#   bash infra/scripts/live-integration.sh           # full bring-up + checks
#   LIVE_RSS=1 bash infra/scripts/live-integration.sh # also fetch a real feed
#   SKIP_INSTALL=1 ...                                 # skip apt install step
#
# Requires outbound network for apt + (optionally) the live RSS fetch.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
LIVE_RSS="${LIVE_RSS:-0}"
SKIP_INSTALL="${SKIP_INSTALL:-0}"
export PATH="$HOME/.local/bin:$PATH"

fail=0
step() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
check() { if [ "$1" -ne 0 ]; then printf '   \033[1;31m[FAIL]\033[0m %s (exit %s)\n' "$2" "$1"; fail=1; else printf '   \033[1;32m[ok]\033[0m %s\n' "$2"; fi; }

# 0. ensure uv exists
if ! command -v uv >/dev/null 2>&1; then
  step "0/8 install uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

step "1/8 services: PostgreSQL(+pgvector), Redis, Kafka"
if [ "$SKIP_INSTALL" != "1" ]; then
  $SUDO bash infra/scripts/dev-services.sh install
fi
$SUDO bash infra/scripts/dev-services.sh up
check $? "services up"

cd backend

step "2/8 uv sync (native C++ + llm + dev)"
uv sync --extra native --extra llm --group dev; check $? "uv sync"

step "3/8 native module import"
uv run python -c "import newskoo_native as n; print('  native simhash:', n.simhash64('hello world'))"; check $? "native import"

step "4/8 alembic upgrade head"
uv run alembic upgrade head; check $? "migrations"

step "5/8 create Kafka topics"
uv run python -m newskoo.core.topics; check $? "kafka topics"

step "6/8 seed worldwide source catalog"
uv run python -m newskoo.sources.seed_cli; check $? "seed sources"

step "7/8 live smoke (DB roundtrip + FTS + pgvector$([ "$LIVE_RSS" = "1" ] && echo ' + real RSS'))"
if [ "$LIVE_RSS" = "1" ]; then
  uv run python -m newskoo.smoke --live-rss
else
  uv run python -m newskoo.smoke
fi
check $? "smoke"

step "8/8 full test suite (native + mocked integration)"
uv run pytest -q; check $? "pytest"

echo
if [ "$fail" -eq 0 ]; then
  printf '\033[1;32m================ LIVE INTEGRATION: ALL GREEN ================\033[0m\n'
else
  printf '\033[1;31m============ LIVE INTEGRATION: FAILURES ABOVE ==============\033[0m\n'
fi
echo "Next: set LLM keys in .env and start the worker fleet (docs/LIVE_INTEGRATION.md)."
exit "$fail"
