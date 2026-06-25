#!/usr/bin/env bash
set -euo pipefail
PORT="${OAM_GATEWAY_PORT:-8787}"
BASE="http://127.0.0.1:${PORT}"

echo "Hub UI doğrulama — ${BASE}/hub"
echo ""

if ! curl -sf "${BASE}/hub/version" >/dev/null; then
  echo "HATA: Hub çalışmıyor. Önce: bash scripts/start_hub.sh"
  exit 1
fi

BUILD=$(curl -s "${BASE}/hub/version" | python3 -c "import sys,json; print(json.load(sys.stdin)['hub_build'])")
HTML=$(curl -s -H 'Cache-Control: no-cache' "${BASE}/hub?v=${BUILD}")

echo "Sunucu build : ${BUILD}"

if [[ "${HTML}" == *featured-worker* ]]; then
  echo "Arayüz        : YENİ (Market-Pulse hero)"
else
  echo "Arayüz        : ESKİ — sunucuyu yeniden başlatın:"
  echo "  lsof -ti :${PORT} | xargs kill -9"
  echo "  bash scripts/start_hub.sh"
  exit 1
fi

if [[ "${HTML}" == *setupAlert* ]]; then
  echo "Mesh uyarısı  : var"
else
  echo "Mesh uyarısı  : yok"
fi

echo ""
echo "Tarayıcıda açın: ${BASE}/hub?v=${BUILD}"
echo "Hâlâ eski görünüyorsa: Ctrl+Shift+R veya gizli pencere"
