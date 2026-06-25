#!/usr/bin/env bash
# axium.com.tr — Hub production (Zinesh ile ilişkisiz)
# Sunucuda root: bash scripts/deploy_axium_production.sh
set -euo pipefail

DOMAIN="${DOMAIN:-axium.com.tr}"
INSTALL_DIR="${INSTALL_DIR:-/opt/fizobia}"
HUB_PORT="${HUB_PORT:-8787}"
REPO="${REPO:-https://github.com/cromles/fizobia.git}"
BRANCH="${BRANCH:-main}"

echo ""
echo "  Axium Hub deploy — ${DOMAIN}"
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
OAM_HUB_DEMO=false
OAM_HUB_LIVE_INTERVAL=30
OAM_X402_ENABLED=true
OAM_X402_DEV_ACCEPT_PROOF=true
OAM_X402_MARKET_PULSE_PRICE=0.05
OAM_X402_SENTIMENT_PRICE=0.04
OAM_X402_MESH_PROOF_PRICE=0.10
OAM_CORS_ORIGINS=https://${DOMAIN},https://www.${DOMAIN}
OAM_EMBED_FRAME_ORIGINS=https://${DOMAIN},https://www.${DOMAIN}
OAM_ONCHAIN_ENABLED=false
EOF

chmod +x scripts/*.sh

# Eski süreçleri kapat
if command -v lsof >/dev/null 2>&1; then
  mapfile -t OLD_PIDS < <(lsof -ti ":${HUB_PORT}" 2>/dev/null | sort -u || true)
  if ((${#OLD_PIDS[@]})); then
    kill -9 "${OLD_PIDS[@]}" 2>/dev/null || true
    sleep 1
  fi
fi

# systemd
cp deploy/oam-hub.service /etc/systemd/system/oam-hub.service
sed -i "s|WorkingDirectory=.*|WorkingDirectory=${INSTALL_DIR}|" /etc/systemd/system/oam-hub.service
sed -i "s|EnvironmentFile=.*|EnvironmentFile=${INSTALL_DIR}/.env.server|" /etc/systemd/system/oam-hub.service
systemctl daemon-reload
systemctl enable oam-hub
systemctl restart oam-hub

sleep 3
if curl -sf "http://127.0.0.1:${HUB_PORT}/hub/version" >/dev/null; then
  BUILD=$(curl -s "http://127.0.0.1:${HUB_PORT}/hub/version" | python3 -c "import sys,json; print(json.load(sys.stdin)['hub_build'])")
  echo ""
  echo "  Hub çalışıyor — build: ${BUILD}"
  echo "  Dahili: http://127.0.0.1:${HUB_PORT}/hub"
  echo ""
  echo "  Son adım — aaPanel / Nginx:"
  echo "    Site ekle: ${DOMAIN}"
  echo "    Reverse proxy → http://127.0.0.1:${HUB_PORT}"
  echo "    SSL: Let's Encrypt (aaPanel'den)"
  echo ""
  echo "  Örnek nginx: deploy/nginx-axium.conf.example"
  echo ""
else
  echo "  HATA: Hub başlamadı"
  journalctl -u oam-hub -n 30 --no-pager
  exit 1
fi
