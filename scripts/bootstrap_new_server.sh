#!/usr/bin/env bash
# Axium — sıfır VPS kurulumu (yeni sunucu migrasyonu)
# Kullanım (root):
#   curl -fsSL https://raw.githubusercontent.com/cromles/fizobia/main/scripts/bootstrap_new_server.sh | bash
#
# Gemini anahtarı ile:
#   AXIUM_GEMINI_KEY="AIza..." bash -c 'curl -fsSL ... | bash'
set -euo pipefail

DOMAIN="${DOMAIN:-axium.com.tr}"
INSTALL_DIR="${INSTALL_DIR:-/opt/fizobia}"
HUB_PORT="${HUB_PORT:-8787}"
SWAP_GB="${SWAP_GB:-2}"
MIN_RAM_MB="${MIN_RAM_MB:-3500}"

echo ""
echo "  ═══════════════════════════════════════"
echo "  Axium — Yeni Sunucu Kurulumu"
echo "  Domain: ${DOMAIN}"
echo "  ═══════════════════════════════════════"
echo ""

if [[ "$(id -u)" -ne 0 ]]; then
  echo "  HATA: root olarak çalıştırın."
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

TOTAL_RAM=$(free -m | awk '/^Mem:/{print $2}')
echo "  RAM: ${TOTAL_RAM} MB"
if (( TOTAL_RAM < MIN_RAM_MB )); then
  echo "  ⚠ Düşük RAM — ${SWAP_GB}GB swap ekleniyor…"
  if [[ ! -f /swapfile ]]; then
    fallocate -l "${SWAP_GB}G" /swapfile 2>/dev/null || dd if=/dev/zero of=/swapfile bs=1M count=$((SWAP_GB * 1024)) status=progress
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  fi
  free -h
fi

echo ""
echo "  [1/5] Paketler kuruluyor…"
apt-get update -qq
apt-get install -y -qq git curl python3 python3-pip lsof nginx certbot python3-certbot-nginx

echo "  [2/5] Kod indiriliyor…"
mkdir -p "${INSTALL_DIR}"
if [[ -d "${INSTALL_DIR}/.git" ]]; then
  cd "${INSTALL_DIR}"
  git fetch origin && git checkout main && git pull origin main
else
  git clone --branch main --depth 1 https://github.com/cromles/fizobia.git "${INSTALL_DIR}"
  cd "${INSTALL_DIR}"
fi
chmod +x scripts/*.sh

if [[ -n "${AXIUM_GEMINI_KEY:-}" ]]; then
  cat > "${INSTALL_DIR}/.env.llm.local" <<EOF
OAM_LLM_API_KEY=${AXIUM_GEMINI_KEY}
OAM_LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
OAM_LLM_MODEL=gemini-2.5-flash
EOF
  chmod 600 "${INSTALL_DIR}/.env.llm.local"
  echo "  ✓ Gemini anahtarı .env.llm.local olarak kaydedildi"
fi

echo "  [3/5] Ekosistem deploy…"
DOMAIN="${DOMAIN}" INSTALL_DIR="${INSTALL_DIR}" HUB_PORT="${HUB_PORT}" bash scripts/deploy_axium_production.sh

echo "  [4/5] Nginx reverse proxy…"
NGINX_SITE="/etc/nginx/sites-available/${DOMAIN}"
cat > "${NGINX_SITE}" <<EOF
server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN};

    location / {
        proxy_pass http://127.0.0.1:${HUB_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 120s;
    }
}
EOF
ln -sf "${NGINX_SITE}" "/etc/nginx/sites-enabled/${DOMAIN}"
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
nginx -t && systemctl enable nginx && systemctl reload nginx

echo "  [5/5] SSL (Let's Encrypt)…"
if [[ -n "${CERTBOT_EMAIL:-}" ]]; then
  CERTBOT_EMAIL="${CERTBOT_EMAIL}" bash scripts/setup_ssl_axium.sh || echo "  SSL atlandı — sonra: cd ${INSTALL_DIR} && bash scripts/setup_ssl_axium.sh"
else
  echo "  SSL atlandı — e-posta ile: CERTBOT_EMAIL=admin@${DOMAIN} bash scripts/setup_ssl_axium.sh"
fi

NEW_IP=$(curl -4 -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')
BUILD=$(curl -sf "http://127.0.0.1:${HUB_PORT}/hub/version" | python3 -c "import sys,json; print(json.load(sys.stdin).get('hub_build','?'))" 2>/dev/null || echo "?")

echo ""
echo "  ═══════════════════════════════════════"
echo "  ✓ Kurulum tamam"
echo "  Build: ${BUILD}"
echo "  Dahili: http://127.0.0.1:${HUB_PORT}/hub"
echo "  Dış IP: ${NEW_IP}"
echo ""
echo "  DNS (Turhost) — axium.com.tr:"
echo "    @   A     → ${NEW_IP}"
echo "    www CNAME → ${DOMAIN}"
echo ""
echo "  DNS yayıldıktan sonra test:"
echo "    curl -s http://${DOMAIN}/hub/version"
echo "    curl -s http://${DOMAIN}/hub/apis"
echo ""
echo "  Gemini yoksa:"
echo "    nano ${INSTALL_DIR}/.env.llm.local"
echo "    systemctl restart oam-ecosystem"
echo "  ═══════════════════════════════════════"
echo ""
