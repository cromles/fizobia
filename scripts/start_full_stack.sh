#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${OAM_GATEWAY_PORT:-8787}"

echo ""
echo "  The Hub — TAM STACK (10 işçi + gateway)"
echo "  http://127.0.0.1:${PORT}/hub"
echo ""

if command -v lsof >/dev/null 2>&1; then
  OLD_PID=$(lsof -ti ":${PORT}" 2>/dev/null | head -1 || true)
  if [[ -n "${OLD_PID}" ]]; then
    echo "  Eski gateway kapatılıyor (PID ${OLD_PID})…"
    kill "${OLD_PID}" 2>/dev/null || true
    sleep 1
  fi
fi

export OAM_HUB_DEMO="${OAM_HUB_DEMO:-false}"
export OAM_HUB_LIVE_INTERVAL="${OAM_HUB_LIVE_INTERVAL:-30}"
export OAM_X402_ENABLED="${OAM_X402_ENABLED:-true}"

python3 -m pip install -q -r requirements.txt
echo "  OAM_HUB_DEMO=${OAM_HUB_DEMO}"
echo "  Ctrl+C ile tüm süreçler durur"
echo ""

exec python3 -m app.run_stack
