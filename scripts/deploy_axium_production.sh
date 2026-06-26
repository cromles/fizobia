#!/usr/bin/env bash
# axium.com.tr — birleşik ekosistem (10 ajan + otopilot)
# Sunucuda root: curl -fsSL https://raw.githubusercontent.com/cromles/fizobia/main/scripts/deploy_axium_production.sh | bash
set -euo pipefail

DOMAIN="${DOMAIN:-axium.com.tr}"
INSTALL_DIR="${INSTALL_DIR:-/opt/fizobia}"
HUB_PORT="${HUB_PORT:-8787}"
REPO="${REPO:-https://github.com/cromles/fizobia.git}"
BRANCH="${BRANCH:-main}"

echo ""
echo "  Axium Ekosistem deploy — ${DOMAIN}"
echo "  10 ajan · medya · sermaye · otopilot 60s"
echo ""

export DEBIAN_FRONTEND=noninteractive
if command -v apt-get >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y -qq git python3 python3-pip lsof curl
fi

mkdir -p "${INSTALL_DIR}"
if [[ -d "${INSTALL_DIR}/.git" ]]; then
  cd "${INSTALL_DIR}"
  git fetch origin
  git checkout "${BRANCH}"
  git pull origin "${BRANCH}"
else
  git clone --branch "${BRANCH}" --depth 1 "${REPO}" "${INSTALL_DIR}"
  cd "${INSTALL_DIR}"
fi

python3 -m pip install -q -r requirements.txt

cat > "${INSTALL_DIR}/.env.server" <<EOF
OAM_GATEWAY_HOST=0.0.0.0
OAM_GATEWAY_PORT=${HUB_PORT}
OAM_PUBLIC_BASE_URL=https://${DOMAIN}
OAM_STACK_MODE=ecosystem
OAM_HUB_DEMO=false
OAM_HUB_LIVE_INTERVAL=30
OAM_AUTOPILOT_ENABLED=true
OAM_AUTOPILOT_INTERVAL=60
OAM_AUTOPILOT_WARMUP=12
OAM_AUTOPILOT_MIN_AGENTS=3
OAM_X402_ENABLED=true
OAM_X402_DEV_ACCEPT_PROOF=true
OAM_X402_MARKET_PULSE_PRICE=0.05
OAM_X402_SENTIMENT_PRICE=0.04
OAM_X402_MESH_PROOF_PRICE=0.10
OAM_CORS_ORIGINS=https://${DOMAIN},https://www.${DOMAIN},http://${DOMAIN},http://www.${DOMAIN}
OAM_EMBED_FRAME_ORIGINS=https://${DOMAIN},https://www.${DOMAIN}
OAM_ONCHAIN_ENABLED=false
EOF

chmod +x scripts/*.sh

# Eski hub süreçlerini kapat
for port in ${HUB_PORT} 8101 8102 8103 8104 8105 8106 8107 8108 8109 8110 8111 8112 8113 8114 8115 8116; do
  lsof -ti ":${port}" 2>/dev/null | xargs -r kill -9 || true
done
sleep 2

# Eski gateway-only servis varsa durdur
systemctl stop oam-hub 2>/dev/null || true
systemctl disable oam-hub 2>/dev/null || true

# Birleşik ekosistem systemd
cp deploy/oam-ecosystem.service /etc/systemd/system/oam-ecosystem.service
sed -i "s|WorkingDirectory=.*|WorkingDirectory=${INSTALL_DIR}|" /etc/systemd/system/oam-ecosystem.service
sed -i "s|EnvironmentFile=.*|EnvironmentFile=${INSTALL_DIR}/.env.server|" /etc/systemd/system/oam-ecosystem.service
systemctl daemon-reload
systemctl enable oam-ecosystem
systemctl restart oam-ecosystem

if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q "Status: active"; then
  ufw allow "${HUB_PORT}/tcp" || true
  ufw allow 8104:8116/tcp || true
fi

echo "  Ajanlar ayağa kalkıyor (20s)…"
sleep 20

if curl -sf "http://127.0.0.1:${HUB_PORT}/hub/version" >/dev/null; then
  BUILD=$(curl -s "http://127.0.0.1:${HUB_PORT}/hub/version" | python3 -c "import sys,json; print(json.load(sys.stdin)['hub_build'])")
  AGENTS=$(curl -s "http://127.0.0.1:${HUB_PORT}/hub/ecosystem" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_agents',0))")
  echo ""
  echo "  ✓ Ekosistem canlı — build: ${BUILD} · ajan: ${AGENTS}"
  echo "  Dahili: http://127.0.0.1:${HUB_PORT}/hub"
  echo ""

  curl -sf -X POST "http://127.0.0.1:${HUB_PORT}/hub/ecosystem/assemble" \
    -H 'Content-Type: application/json' \
    -d '{"symbol":"bitcoin"}' >/dev/null && echo "  ✓ İlk ekosistem birleştirme tamam" || true

  echo ""
  echo "  aaPanel / Nginx:"
  echo "    Site: ${DOMAIN} → reverse proxy http://127.0.0.1:${HUB_PORT}"
  echo "    SSL: Let's Encrypt"
  echo ""
  echo "  Durum: systemctl status oam-ecosystem"
  echo "  Log:   journalctl -u oam-ecosystem -f"
  echo ""
else
  echo "  HATA: Hub yanıt vermiyor"
  journalctl -u oam-ecosystem -n 40 --no-pager
  exit 1
fi
