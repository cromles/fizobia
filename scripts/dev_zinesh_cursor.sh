#!/usr/bin/env bash
# Cursor'da Zinesh + Hub birlikte çalıştırma
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export OAM_HUB_DEMO=false
export OAM_PUBLIC_BASE_URL=http://127.0.0.1:8787
export OAM_CORS_ORIGINS="http://127.0.0.1:3000,http://localhost:3000,https://zinesh.com,https://www.zinesh.com"

echo "════════════════════════════════════════"
echo "  Zinesh (3000) + OAM Hub (8787)"
echo "════════════════════════════════════════"
echo ""
echo "  Zinesh site:  http://127.0.0.1:3000"
echo "  Hub API:      http://127.0.0.1:8787/hub/sdk/config"
echo "  Hub embed:    http://127.0.0.1:8787/hub/embed"
echo ""
echo "  Cursor: fizobia-zinesh.code-workspace dosyasını açın"
echo ""

python3 -m app.run_stack &
STACK_PID=$!
sleep 4

cd zinesh-web
python3 -m http.server 3000 &
WEB_PID=$!

cleanup() {
  kill "$STACK_PID" "$WEB_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

wait
