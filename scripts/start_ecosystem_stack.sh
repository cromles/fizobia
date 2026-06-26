#!/usr/bin/env bash
# Birleşik ekosistem — kurucular + medya + sermaye ajanları
set -euo pipefail
cd "$(dirname "$0")/.."

export OAM_STACK_MODE=ecosystem
export OAM_HUB_DEMO=false
export OAM_HUB_LIVE_INTERVAL="${OAM_HUB_LIVE_INTERVAL:-30}"
export OAM_AUTOPILOT_ENABLED="${OAM_AUTOPILOT_ENABLED:-true}"
export OAM_AUTOPILOT_INTERVAL="${OAM_AUTOPILOT_INTERVAL:-60}"
export OAM_AUTOPILOT_WARMUP="${OAM_AUTOPILOT_WARMUP:-12}"
export OAM_X402_ENABLED=true

if [[ -f .env.server ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env.server
  set +a
fi

echo ""
echo "  Axium — Birleşik Ekosistem"
echo "  15 mikro ajan: kurucular + medya + sermaye + departman işçileri"
echo "  Birleştir: POST /hub/ecosystem/assemble"
echo ""

exec python3 -m app.run_stack
