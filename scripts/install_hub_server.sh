#!/usr/bin/env bash
# Hub sunucusunda root olarak: HUB_IP=1.2.3.4 bash scripts/install_hub_server.sh
# veya: bash scripts/install_hub_server.sh 1.2.3.4
set -euo pipefail

HUB_IP="${HUB_IP:-${1:-}}"
HUB_PORT="${HUB_PORT:-8787}"
INSTALL_DIR="${INSTALL_DIR:-/opt/fizobia}"
REPO="${REPO:-https://github.com/cromles/fizobia.git}"
BRANCH="${BRANCH:-main}"

if [[ -z "${HUB_IP}" ]]; then
  echo "Kullanım: HUB_IP=SUNUCU_IP bash scripts/install_hub_server.sh"
  echo "   veya: bash scripts/install_hub_server.sh SUNUCU_IP"
  exit 1
fi

echo ""
echo "  OAM Hub kurulumu — ${HUB_IP}"
echo ""

export DEBIAN_FRONTEND=noninteractive
if command -v apt-get >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y -qq git python3 python3-pip python3-venv lsof curl
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
OAM_PUBLIC_BASE_URL=http://${HUB_IP}:${HUB_PORT}
OAM_HUB_DEMO=false
OAM_HUB_LIVE_INTERVAL=30
OAM_X402_ENABLED=true
OAM_X402_DEV_ACCEPT_PROOF=true
OAM_X402_MARKET_PULSE_PRICE=0.05
OAM_CORS_ORIGINS=http://${HUB_IP}:${HUB_PORT},http://127.0.0.1:${HUB_PORT}
OAM_EMBED_FRAME_ORIGINS=http://${HUB_IP}:${HUB_PORT}
OAM_ONCHAIN_ENABLED=false
EOF

chmod +x scripts/*.sh

if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q "Status: active"; then
  ufw allow "${HUB_PORT}/tcp" || true
  ufw allow 8101:8110/tcp || true
fi

lsof -ti ":${HUB_PORT}" 2>/dev/null | xargs -r kill -9 || true

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
  echo "  Kurulum tamam — build: ${BUILD}"
  echo "  Hub: http://${HUB_IP}:${HUB_PORT}/hub"
  echo "  Durum: systemctl status oam-hub"
  echo ""
else
  echo "  HATA: Hub yanıt vermiyor. Log: journalctl -u oam-hub -n 50"
  exit 1
fi
