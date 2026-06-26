#!/usr/bin/env bash
# Sunucu IP/SSH gelene kadar son kontrol + deploy komut kartı
set -euo pipefail
cd "$(dirname "$0")/.."

DOMAIN="${DOMAIN:-axium.com.tr}"
HUB_PORT="${HUB_PORT:-8787}"
SERVER_IP="${SERVER_IP:-}"
SERVER_USER="${SERVER_USER:-root}"

echo ""
echo "  Axium — Sunucu Öncesi Hazırlık"
echo "  ================================="
echo ""

bash scripts/pre_server_check.sh

AGENTS=$(python3 -c "from app.mesh.ecosystem_registry import ECOSYSTEM_STACK_AGENT_IDS; print(len(ECOSYSTEM_STACK_AGENT_IDS))")
echo ""
echo "  Ekosistem: ${AGENTS} mikro ajan · 3 departman · makale + arena + mesh proof"
echo ""

if [[ -n "${SERVER_IP}" ]]; then
  echo "  [1/3] SSH bağlantı testi → ${SERVER_USER}@${SERVER_IP}"
  if ssh -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new "${SERVER_USER}@${SERVER_IP}" "echo ok" 2>/dev/null; then
    echo "  ✓ SSH erişilebilir"
    echo ""
    echo "  [2/3] Uzak deploy başlatılıyor…"
    ssh "${SERVER_USER}@${SERVER_IP}" \
      "curl -fsSL https://raw.githubusercontent.com/cromles/fizobia/main/scripts/deploy_axium_production.sh | bash -s --"
    echo ""
    echo "  [3/3] DNS: ${DOMAIN} → ${SERVER_IP}"
    echo "  Nginx reverse proxy → 127.0.0.1:${HUB_PORT}"
    echo "  Test: curl -s https://${DOMAIN}/hub/departments"
  else
    echo "  ✗ SSH bağlanamadı — IP veya anahtar/şifreyi kontrol edin"
    exit 1
  fi
else
  echo "  Sunucu bilgisi henüz yok. IP gelince:"
  echo ""
  echo "  export SERVER_IP=<VDS_IP>"
  echo "  export SERVER_USER=root"
  echo "  bash scripts/ready_for_server.sh"
  echo ""
  echo "  Veya sunucuda doğrudan:"
  echo "  curl -fsSL https://raw.githubusercontent.com/cromles/fizobia/main/scripts/deploy_axium_production.sh | bash"
  echo ""
  echo "  DNS: ${DOMAIN} → <VDS_IP>"
  echo "  Nginx: reverse proxy http://127.0.0.1:${HUB_PORT}"
  echo "  SSL: Let's Encrypt (aaPanel veya certbot)"
  echo ""
  echo "  Deploy sonrası doğrulama:"
  echo "  curl -s https://${DOMAIN}/hub/version"
  echo "  curl -s https://${DOMAIN}/hub/departments"
  echo "  PYTHONPATH=. python3 scripts/demo_departments_simulation.py"
  echo ""
  echo "  On-chain (opsiyonel):"
  echo "  bash scripts/deploy_base_sepolia.sh"
  echo "  # .env.onchain.example → .env.server"
  echo ""
fi
