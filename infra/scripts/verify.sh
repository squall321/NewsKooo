#!/usr/bin/env bash
# Consolidated backend verification in WSL: sync deps (incl. native C++ build +
# llm extra), lint, type-check, test. venv lives in the Linux home (not /mnt/d)
# to avoid slow I/O and Windows/Linux binary mixing.
set -uo pipefail

export HOME=/root
export PATH="/root/.local/bin:$PATH"
export UV_PROJECT_ENVIRONMENT=/root/venvs/newskoo
cd /mnt/d/NewsKoo/backend

echo "=================== uv sync (native + llm + dev) ==================="
uv sync --extra native --extra llm --group dev
SYNC=$?
echo "SYNC_EXIT=$SYNC"

echo "=================== ruff check ==================="
uv run ruff check . ; echo "RUFF_EXIT=$?"

echo "=================== pytest ==================="
uv run pytest -q ; echo "PYTEST_EXIT=$?"

echo "=================== native import check ==================="
uv run python -c "import newskoo_native as n; print('native OK simhash=', n.simhash64('hello world'))" \
  && echo "NATIVE_OK" || echo "NATIVE_IMPORT_FAILED"
echo "=================== done ==================="
