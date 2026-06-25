#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

PORT="${OAM_GATEWAY_PORT:-8787}"

echo ""
echo "  The Hub (Nebula UI) — http://127.0.0.1:${PORT}/hub"
echo "  Not: Sadece gateway — mesh için: bash scripts/start_full_stack.sh"
echo ""

# Porttaki TÜM eski süreçleri kapat (tek PID yetmez — eski arayüz kalır)
if command -v lsof >/dev/null 2>&1; then
  mapfile -t OLD_PIDS < <(lsof -ti ":${PORT}" 2>/dev/null | sort -u || true)
  if ((${#OLD_PIDS[@]})); then
    echo "  Eski süreç(ler) kapatılıyor: ${OLD_PIDS[*]}"
    kill -9 "${OLD_PIDS[@]}" 2>/dev/null || true
    sleep 1
  fi
fi
if lsof -ti ":${PORT}" >/dev/null 2>&1; then
  echo "  HATA: Port ${PORT} hâlâ dolu. Elle kapatın:"
  echo "    lsof -ti :${PORT} | xargs kill -9"
  exit 1
fi

export OAM_HUB_DEMO="${OAM_HUB_DEMO:-false}"
export OAM_HUB_LIVE_INTERVAL="${OAM_HUB_LIVE_INTERVAL:-30}"

python3 -m pip install -q -r requirements.txt
echo "  OAM_HUB_DEMO=${OAM_HUB_DEMO}"
echo "  Başlatılıyor… (Ctrl+C ile dur)"
echo ""

exec python3 -m app.main
