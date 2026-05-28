#!/usr/bin/env bash
# NewsKoo dev environment bootstrap for WSL Ubuntu (dev: 20.04, prod: 22.04).
# Installs core build toolchain, uv-managed Python 3.13, and Node 22 LTS.
# Idempotent-ish: safe to re-run. Run as root inside WSL.
set -euo pipefail

# WSL interop can leak a Windows-style $HOME; force a sane Linux home.
export HOME=/root
export DEBIAN_FRONTEND=noninteractive
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

log() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }

log "apt update + core build toolchain"
apt-get update -y
apt-get install -y --no-install-recommends \
  build-essential cmake ninja-build pkg-config \
  git curl wget ca-certificates gnupg lsb-release unzip xz-utils \
  libssl-dev zlib1g-dev libffi-dev

log "Install uv (Python toolchain manager)"
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin:$PATH"

log "Install Python 3.13 via uv"
uv python install 3.13
uv python pin 3.13 || true

log "Install Node.js 22 LTS via NodeSource"
if ! command -v node >/dev/null 2>&1 || [ "$(node -v 2>/dev/null | cut -d. -f1)" != "v22" ]; then
  curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
  apt-get install -y nodejs
fi
corepack enable || true

log "Versions"
echo "gcc:   $(gcc --version | head -n1)"
echo "g++:   $(g++ --version | head -n1)"
echo "cmake: $(cmake --version | head -n1)"
echo "uv:    $(uv --version)"
echo "py313: $(uv run --python 3.13 python -V 2>/dev/null || true)"
echo "node:  $(node -v)"
echo "npm:   $(npm -v)"

log "dev-bootstrap complete"
