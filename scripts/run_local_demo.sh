#!/usr/bin/env bash
# Lokal tam demo — gateway + mesh proof (ajan süreçleri olmadan x402 çalışır)
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${OAM_GATEWAY_PORT:-8787}"

if lsof -ti ":${PORT}" >/dev/null 2>&1; then
  echo "Hub zaten çalışıyor :${PORT}"
else
  echo "Hub başlatılıyor…"
  OAM_HUB_DEMO=false OAM_HUB_LIVE_INTERVAL=0 python3 -m app.main &
  HUB_PID=$!
  trap 'kill $HUB_PID 2>/dev/null || true' EXIT
  for i in $(seq 1 30); do
    curl -sf "http://127.0.0.1:${PORT}/hub/version" >/dev/null && break
    sleep 0.5
  done
fi

echo ""
python3 scripts/demo_mesh_proof.py
echo ""
python3 scripts/demo_x402_market_pulse.py bitcoin
echo ""
echo "  Paylaşım kartı linki yukarıda (PAYLAŞ satırı)."
echo ""
