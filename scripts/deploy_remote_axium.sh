#!/usr/bin/env bash
# Uzaktan Axium deploy — Cursor Secrets: AXIUM_SSH_PASSWORD
set -euo pipefail

SERVER_IP="${AXIUM_SERVER_IP:-89.47.113.150}"
SERVER_USER="${AXIUM_SERVER_USER:-root}"
PASS="${AXIUM_SSH_PASSWORD:-${SERVER_SSH_PASSWORD:-${SSH_PASSWORD:-}}}"

if [[ -z "${PASS}" ]]; then
  echo "HATA: AXIUM_SSH_PASSWORD tanımlı değil."
  echo "Cursor → Secrets → AXIUM_SSH_PASSWORD = sunucu root şifresi"
  exit 1
fi

if ! command -v sshpass >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq && apt-get install -y -qq sshpass
fi

echo "  Uzak deploy → ${SERVER_USER}@${SERVER_IP}"

sshpass -p "${PASS}" ssh \
  -o StrictHostKeyChecking=accept-new \
  -o PreferredAuthentications=password \
  -o PubkeyAuthentication=no \
  "${SERVER_USER}@${SERVER_IP}" \
  'curl -fsSL https://raw.githubusercontent.com/cromles/fizobia/main/scripts/deploy_axium_production.sh | bash -s --'

echo ""
echo "  SSL kurulumu (opsiyonel)…"
sshpass -p "${PASS}" ssh \
  -o StrictHostKeyChecking=accept-new \
  -o PreferredAuthentications=password \
  -o PubkeyAuthentication=no \
  "${SERVER_USER}@${SERVER_IP}" \
  "cd /opt/fizobia && git pull -q origin main && bash scripts/setup_ssl_axium.sh" \
  || echo "  SSL atlandı veya başarısız — HTTP ile devam"

echo ""
echo "  Doğrulama:"
curl -sS --connect-timeout 10 "http://${SERVER_IP}:${HUB_PORT:-8787}/hub/version" || true
curl -sS --connect-timeout 10 "http://axium.com.tr/hub/version" || true
echo ""
