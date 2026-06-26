#!/usr/bin/env bash
# Kurucu ajan yığını — 3 işçi + 1 koordinatör (Zinesh/mock yok)
set -euo pipefail
cd "$(dirname "$0")/.."

export OAM_STACK_MODE=founder
export OAM_HUB_DEMO=false
export OAM_HUB_LIVE_INTERVAL="${OAM_HUB_LIVE_INTERVAL:-30}"
export OAM_X402_ENABLED=true

if [[ -f .env.server ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env.server
  set +a
fi

echo ""
echo "  Axium — Kurucu Ajan Ekosistemi"
echo "  3 kurucu işçi + 1 koordinatör → mesh büyür"
echo ""

exec python3 -m app.run_stack
