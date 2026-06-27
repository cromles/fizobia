#!/usr/bin/env bash
# axium.com.tr — birleşik ekosistem deploy (LLM anahtarını korur)
set -euo pipefail

DOMAIN="${DOMAIN:-axium.com.tr}"
INSTALL_DIR="${INSTALL_DIR:-/opt/fizobia}"
HUB_PORT="${HUB_PORT:-8787}"
REPO="${REPO:-https://github.com/cromles/fizobia.git}"
BRANCH="${BRANCH:-main}"

echo ""
echo "  Axium Ekosistem deploy — ${DOMAIN}"
echo "  12 kalifiye ajan (15 arka plan) · 3 departman · ücretsiz API"
echo ""

export DEBIAN_FRONTEND=noninteractive
if command -v apt-get >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y -qq git python3 python3-pip lsof curl
fi

mkdir -p "${INSTALL_DIR}"
ENV_FILE="${INSTALL_DIR}/.env.server"
LLM_BACKUP_FILE="$(mktemp)"
EXTRA_BACKUP_FILE="$(mktemp)"

if [[ -f "${ENV_FILE}" ]]; then
  grep -E '^OAM_LLM_' "${ENV_FILE}" > "${LLM_BACKUP_FILE}" 2>/dev/null || true
  grep -E '^OAM_ONCHAIN_|^OAM_X402_PAYEE|^OAM_X402_USDC' "${ENV_FILE}" > "${EXTRA_BACKUP_FILE}" 2>/dev/null || true
fi

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

if [[ -f /etc/letsencrypt/live/${DOMAIN}/fullchain.pem ]]; then
  PUBLIC_BASE="https://${DOMAIN}"
else
  PUBLIC_BASE="http://${DOMAIN}"
fi

cat > "${ENV_FILE}" <<EOF
OAM_GATEWAY_HOST=0.0.0.0
OAM_GATEWAY_PORT=${HUB_PORT}
OAM_PUBLIC_BASE_URL=${PUBLIC_BASE}
OAM_STACK_MODE=ecosystem
OAM_HUB_DEMO=false
OAM_HUB_REVENUE_STORE=${INSTALL_DIR}/data/hub_revenue.jsonl
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
OAM_X402_ARENA_PRICE=0.10
OAM_PURGE_EVERY_CYCLES=12
OAM_CORS_ORIGINS=https://${DOMAIN},https://www.${DOMAIN},http://${DOMAIN},http://www.${DOMAIN}
OAM_EMBED_FRAME_ORIGINS=https://${DOMAIN},https://www.${DOMAIN}
OAM_ONCHAIN_ENABLED=false
EOF

if [[ -s "${LLM_BACKUP_FILE}" ]]; then
  echo "" >> "${ENV_FILE}"
  echo "# LLM — önceki deploy'dan korundu" >> "${ENV_FILE}"
  cat "${LLM_BACKUP_FILE}" >> "${ENV_FILE}"
elif [[ -f "${INSTALL_DIR}/.env.llm.local" ]]; then
  echo "" >> "${ENV_FILE}"
  echo "# LLM — .env.llm.local" >> "${ENV_FILE}"
  grep -E '^OAM_LLM_' "${INSTALL_DIR}/.env.llm.local" >> "${ENV_FILE}" || true
fi

if [[ -s "${EXTRA_BACKUP_FILE}" ]]; then
  echo "" >> "${ENV_FILE}"
  echo "# On-chain / x402 — önceki deploy'dan korundu" >> "${ENV_FILE}"
  cat "${EXTRA_BACKUP_FILE}" >> "${ENV_FILE}"
fi

rm -f "${LLM_BACKUP_FILE}" "${EXTRA_BACKUP_FILE}"

chmod +x scripts/*.sh

for port in ${HUB_PORT} 8101 8102 8103 8104 8105 8106 8107 8108 8109 8110 8111 8112 8113 8114 8115 8116 8117 8118 8119 8120 8121 8122 8123 8124; do
  lsof -ti ":${port}" 2>/dev/null | xargs -r kill -9 || true
done
sleep 2

systemctl stop oam-hub 2>/dev/null || true
systemctl disable oam-hub 2>/dev/null || true

cp deploy/oam-ecosystem.service /etc/systemd/system/oam-ecosystem.service
sed -i "s|WorkingDirectory=.*|WorkingDirectory=${INSTALL_DIR}|" /etc/systemd/system/oam-ecosystem.service
sed -i "s|EnvironmentFile=.*|EnvironmentFile=${ENV_FILE}|" /etc/systemd/system/oam-ecosystem.service
systemctl daemon-reload
systemctl enable oam-ecosystem
systemctl restart oam-ecosystem

if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q "Status: active"; then
  ufw allow "${HUB_PORT}/tcp" || true
  ufw allow 8104:8124/tcp || true
fi

echo "  Ajanlar ayağa kalkıyor (22s)…"
sleep 22

if curl -sf "http://127.0.0.1:${HUB_PORT}/hub/version" >/dev/null; then
  BUILD=$(curl -s "http://127.0.0.1:${HUB_PORT}/hub/version" | python3 -c "import sys,json; print(json.load(sys.stdin)['hub_build'])")
  AGENTS=$(curl -s "http://127.0.0.1:${HUB_PORT}/hub/ecosystem" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_agents',0))")
  LLM=$(curl -s "http://127.0.0.1:${HUB_PORT}/hub/llm" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('provider','off') if d.get('enabled') else 'template')")
  echo ""
  echo "  ✓ Ekosistem canlı — build: ${BUILD} · ajan: ${AGENTS} · LLM: ${LLM}"
  echo "  Dahili: http://127.0.0.1:${HUB_PORT}/hub"
  echo ""

  curl -sf -X POST "http://127.0.0.1:${HUB_PORT}/hub/ecosystem/assemble" \
    -H 'Content-Type: application/json' \
    -d '{"symbol":"bitcoin"}' >/dev/null && echo "  ✓ İlk ekosistem birleştirme tamam" || true

  DEPTS=$(curl -s "http://127.0.0.1:${HUB_PORT}/hub/departments" | python3 -c "import sys,json; print(json.load(sys.stdin).get('count',0))" 2>/dev/null || echo 0)
  echo "  ✓ Departmanlar: ${DEPTS} kategori"

  if curl -sf "http://127.0.0.1:${HUB_PORT}/hub/apis" >/dev/null 2>&1; then
    APIS=$(curl -s "http://127.0.0.1:${HUB_PORT}/hub/apis" | python3 -c "import sys,json; print(json.load(sys.stdin).get('free_no_auth',0))" 2>/dev/null || echo "?")
    echo "  ✓ Ücretsiz API kaynakları: ${APIS}"
  fi

  echo ""
  echo "  Nginx: ${DOMAIN} → reverse proxy http://127.0.0.1:${HUB_PORT}"
  echo "  SSL:   bash scripts/setup_ssl_axium.sh"
  echo "  Durum: systemctl status oam-ecosystem"
  echo "  Log:   journalctl -u oam-ecosystem -f"
  echo ""
else
  echo "  HATA: Hub yanıt vermiyor"
  journalctl -u oam-ecosystem -n 40 --no-pager
  exit 1
fi
