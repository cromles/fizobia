#!/usr/bin/env bash
# axium.com.tr — Let's Encrypt SSL (Nginx / aaPanel)
set -euo pipefail

DOMAIN="${DOMAIN:-axium.com.tr}"
EMAIL="${CERTBOT_EMAIL:-admin@${DOMAIN}}"
HUB_PORT="${HUB_PORT:-8787}"
INSTALL_DIR="${INSTALL_DIR:-/opt/fizobia}"

echo "  [0/4] Certbot bağımlılık düzeltmesi (pip cryptography çakışması)…"
pip3 uninstall -y cryptography pyopenssl 2>/dev/null || true
apt-get install -y -qq --reinstall python3-openssl python3-cryptography python3-certbot-nginx certbot 2>/dev/null || true

echo ""
echo "  Axium SSL — ${DOMAIN}"
echo ""

export DEBIAN_FRONTEND=noninteractive

if ! command -v nginx >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y -qq nginx
fi

if ! command -v certbot >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y -qq certbot python3-certbot-nginx || apt-get install -y -qq certbot
fi

NGINX_SITE="/etc/nginx/sites-available/${DOMAIN}"
NGINX_ENABLED="/etc/nginx/sites-enabled/${DOMAIN}"

if [[ ! -f "${NGINX_SITE}" ]]; then
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
  ln -sf "${NGINX_SITE}" "${NGINX_ENABLED}"
  rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
  nginx -t
  systemctl reload nginx || systemctl restart nginx
fi

certbot --nginx -d "${DOMAIN}" -d "www.${DOMAIN}" \
  --non-interactive --agree-tos -m "${EMAIL}" \
  --redirect || {
    echo "  certbot --nginx başarısız — standalone deneniyor…"
    systemctl stop nginx
    certbot certonly --standalone -d "${DOMAIN}" -d "www.${DOMAIN}" \
      --non-interactive --agree-tos -m "${EMAIL}"
    systemctl start nginx
  }

if [[ -f /etc/letsencrypt/live/${DOMAIN}/fullchain.pem ]]; then
  if [[ -f "${INSTALL_DIR}/.env.server" ]]; then
    sed -i "s|^OAM_PUBLIC_BASE_URL=.*|OAM_PUBLIC_BASE_URL=https://${DOMAIN}|" "${INSTALL_DIR}/.env.server"
    systemctl restart oam-ecosystem 2>/dev/null || true
  fi
  echo ""
  echo "  ✓ SSL aktif — https://${DOMAIN}/hub"
  echo ""
else
  echo "  HATA: Sertifika oluşturulamadı"
  exit 1
fi
