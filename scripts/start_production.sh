#!/usr/bin/env bash
# Hub production başlatıcı — .env.server dosyasını okur
set -euo pipefail
cd "$(dirname "$0")/.."

ENV_FILE="${OAM_ENV_FILE:-.env.server}"
PORT="${OAM_GATEWAY_PORT:-8787}"

if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
  echo "  Ortam: ${ENV_FILE}"
else
  echo "  UYARI: ${ENV_FILE} yok — varsayılan 127.0.0.1 kullanılır"
  echo "  Sunucu için: cp .env.server.example .env.server && nano .env.server"
fi

if [[ -z "${OAM_PUBLIC_BASE_URL:-}" ]]; then
  echo "  HATA: OAM_PUBLIC_BASE_URL tanımlı değil (.env.server içinde sunucu IP yazın)"
  exit 1
fi

echo ""
echo "  The Hub — ${OAM_PUBLIC_BASE_URL}/hub"
echo ""

if command -v lsof >/dev/null 2>&1; then
  mapfile -t OLD_PIDS < <(lsof -ti ":${PORT}" 2>/dev/null | sort -u || true)
  if ((${#OLD_PIDS[@]})); then
    echo "  Eski süreç(ler) kapatılıyor: ${OLD_PIDS[*]}"
    kill -9 "${OLD_PIDS[@]}" 2>/dev/null || true
    sleep 1
  fi
fi

python3 -m pip install -q -r requirements.txt
echo "  OAM_PUBLIC_BASE_URL=${OAM_PUBLIC_BASE_URL}"
echo "  Tam mesh: bash scripts/start_full_stack.sh (aynı .env.server ile)"
echo ""

exec python3 -m app.main
