#!/usr/bin/env bash
# İlk kurulum: bağımlılıklar + .env.server şablonu + firewall notu
set -euo pipefail
cd "$(dirname "$0")/.."

echo ""
echo "  OAM Hub — sunucu kurulumu (domain gerekmez, IP yeterli)"
echo ""

python3 -m pip install -q -r requirements.txt

if [[ ! -f .env.server ]]; then
  cp .env.server.example .env.server
  echo "  .env.server oluşturuldu — sunucu IP'nizi düzenleyin:"
  echo "    nano .env.server"
  echo ""
fi

PUBLIC=$(grep -E '^OAM_PUBLIC_BASE_URL=' .env.server 2>/dev/null | cut -d= -f2- || echo "")
if [[ "${PUBLIC}" == *"185.12.34.56"* ]] || [[ -z "${PUBLIC}" ]]; then
  echo "  ÖNEMLİ: .env.server içinde OAM_PUBLIC_BASE_URL değerini gerçek sunucu IP'nize yazın"
  echo "  Örnek: OAM_PUBLIC_BASE_URL=http://SUNUCU_IP:8787"
  echo ""
fi

chmod +x scripts/start_production.sh scripts/start_full_stack.sh scripts/verify_hub_ui.sh 2>/dev/null || true

echo "  Firewall (ufw örneği):"
echo "    sudo ufw allow 8787/tcp"
echo "    sudo ufw allow 8101:8110/tcp   # tam mesh için"
echo ""
echo "  Başlat:"
echo "    bash scripts/start_production.sh"
echo ""
echo "  Tam stack (10 işçi + gateway):"
echo "    OAM_ENV_FILE=.env.server bash scripts/start_full_stack.sh"
echo ""
echo "  Doğrula:"
echo "    bash scripts/verify_hub_ui.sh"
echo ""
