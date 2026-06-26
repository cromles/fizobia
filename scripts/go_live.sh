#!/usr/bin/env bash
# Yerelde veya sunucuda: ekosistem stack + ilk birleştirme
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${OAM_GATEWAY_PORT:-8787}"
BASE="http://127.0.0.1:${PORT}"

echo ""
echo "  Axium — Go Live"
echo ""

# Eski gateway-only süreçleri kapat
for port in ${PORT} 8104 8105 8106 8107 8108 8109 8110 8111 8112 8113 8114 8115 8116; do
  lsof -ti ":${port}" 2>/dev/null | xargs -r kill -9 || true
done
sleep 1

if ! curl -sf "${BASE}/hub/version" >/dev/null 2>&1; then
  echo "  Stack başlatılıyor…"
  SESSION="axium-live"
  if command -v tmux >/dev/null 2>&1; then
  tmux -f /exec-daemon/tmux.portal.conf kill-session -t "$SESSION" 2>/dev/null || true
  tmux -f /exec-daemon/tmux.portal.conf new-session -d -s "$SESSION" -c "$PWD" -- bash scripts/start_ecosystem_stack.sh
  else
    nohup bash scripts/start_ecosystem_stack.sh >/tmp/axium-ecosystem.log 2>&1 &
  fi
  for i in $(seq 1 30); do
    curl -sf "${BASE}/hub/version" >/dev/null 2>&1 && break
    sleep 2
  done
fi

if ! curl -sf "${BASE}/hub/version" >/dev/null; then
  echo "  HATA: Hub açılmadı. Log: /tmp/axium-ecosystem.log"
  exit 1
fi

BUILD=$(curl -s "${BASE}/hub/version" | python3 -c "import sys,json; print(json.load(sys.stdin)['hub_build'])")
AGENTS=$(curl -s "${BASE}/hub/ecosystem" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_agents',0))")
echo "  Hub: ${BUILD} · ${AGENTS} ajan"

echo "  Ekosistem birleştiriliyor…"
RESULT=$(curl -sf -X POST "${BASE}/hub/ecosystem/assemble" \
  -H 'Content-Type: application/json' \
  -d '{"symbol":"bitcoin"}')
echo "$RESULT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('  Kanıt:', d.get('proof_id','—'))
print('  Birleştirme:', d.get('assembly_id','—'))
print('  Sermaye:', d.get('capital_readiness','—'))
"

AP=$(curl -s "${BASE}/hub/autopilot" | python3 -c "import sys,json; d=json.load(sys.stdin); print(('aktif' if d.get('running') else 'kapalı') + ' · ' + str(d.get('cycles_completed',0)) + ' döngü')")
echo "  Otopilot: ${AP}"
echo ""
echo "  → ${BASE}/hub"
echo ""
