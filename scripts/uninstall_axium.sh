#!/usr/bin/env bash
# Axium Hub — sunucudan tamamen kaldır (Zinesh / aaPanel / diğer sitelere dokunmaz)
# Kullanım (root):
#   curl -fsSL https://raw.githubusercontent.com/cromles/fizobia/main/scripts/uninstall_axium.sh | bash
#
# Kod klasörünü de silmek için:
#   REMOVE_DATA=1 bash -c 'curl -fsSL ... | bash'
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/fizobia}"
DOMAIN="${DOMAIN:-axium.com.tr}"
HUB_PORT="${HUB_PORT:-8787}"
REMOVE_DATA="${REMOVE_DATA:-0}"

echo ""
echo "  Axium kaldırılıyor — ${DOMAIN}"
echo "  (Zinesh ve diğer siteler etkilenmez)"
echo ""

if [[ "$(id -u)" -ne 0 ]]; then
  echo "  HATA: root olarak çalıştırın."
  exit 1
fi

echo "  [1/4] Servisler durduruluyor…"
systemctl stop oam-ecosystem 2>/dev/null || true
systemctl disable oam-ecosystem 2>/dev/null || true
systemctl stop oam-hub 2>/dev/null || true
systemctl disable oam-hub 2>/dev/null || true

if [[ -f /etc/systemd/system/oam-ecosystem.service ]]; then
  rm -f /etc/systemd/system/oam-ecosystem.service
fi
if [[ -f /etc/systemd/system/oam-hub.service ]]; then
  rm -f /etc/systemd/system/oam-hub.service
fi
systemctl daemon-reload

echo "  [2/4] İşçi portları kapatılıyor…"
for port in ${HUB_PORT} 8101 8102 8103 8104 8105 8106 8107 8108 8109 8110 8111 8112 8113 8114 8115 8116 8117 8118 8119 8120 8121 8122 8123 8124; do
  lsof -ti ":${port}" 2>/dev/null | xargs -r kill -9 || true
done
pkill -f "app.run_stack" 2>/dev/null || true
pkill -f "app.api.main" 2>/dev/null || true
sleep 2

echo "  [3/4] Nginx Axium site config (varsa)…"
for f in \
  "/etc/nginx/sites-enabled/${DOMAIN}" \
  "/etc/nginx/sites-available/${DOMAIN}" \
  "/www/server/panel/vhost/nginx/${DOMAIN}.conf"; do
  if [[ -f "${f}" ]]; then
    rm -f "${f}"
    echo "    silindi: ${f}"
  fi
done
if command -v nginx >/dev/null 2>&1; then
  nginx -t 2>/dev/null && systemctl reload nginx 2>/dev/null || true
fi

echo "  [4/4] Dosyalar…"
if [[ "${REMOVE_DATA}" == "1" ]]; then
  rm -rf "${INSTALL_DIR}"
  echo "    ${INSTALL_DIR} silindi"
else
  echo "    ${INSTALL_DIR} korundu (silmek için: REMOVE_DATA=1)"
fi

FREE=$(free -h | awk '/^Mem:/{print $4}')
echo ""
echo "  ✓ Axium bu sunucudan kaldırıldı"
echo "  Boş RAM (yaklaşık): ${FREE}"
echo ""
echo "  Sonraki adım — yeni sunucuda:"
echo "  curl -fsSL https://raw.githubusercontent.com/cromles/fizobia/main/scripts/bootstrap_new_server.sh | bash"
echo ""
