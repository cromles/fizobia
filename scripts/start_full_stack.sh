#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

ENV_FILE="${OAM_ENV_FILE:-.env.server}"
PORT="${OAM_GATEWAY_PORT:-8787}"

if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

echo ""
echo "  The Hub — TAM STACK (10 işçi + gateway)"
echo "  ${OAM_PUBLIC_BASE_URL:-http://127.0.0.1:${PORT}}/hub"
echo ""

if command -v lsof >/dev/null 2>&1; then
  mapfile -t OLD_PIDS < <(lsof -ti ":${PORT}" 2>/dev/null | sort -u || true)
  if ((${#OLD_PIDS[@]})); then
    echo "  Eski gateway kapatılıyor: ${OLD_PIDS[*]}"
    kill -9 "${OLD_PIDS[@]}" 2>/dev/null || true
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
