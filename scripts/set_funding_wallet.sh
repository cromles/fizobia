#!/usr/bin/env bash
# Axium — fonlama cüzdanını payee + deployer hedefi olarak ayarla
set -euo pipefail

WALLET="${1:-}"
INSTALL_DIR="${INSTALL_DIR:-/opt/fizobia}"

if [[ -z "${WALLET}" ]]; then
  echo "Kullanım: bash scripts/set_funding_wallet.sh 0x..."
  exit 1
fi

if [[ ! "${WALLET}" =~ ^0x[0-9a-fA-F]{40}$ ]]; then
  echo "Geçersiz adres: ${WALLET}"
  exit 1
fi

cd "${INSTALL_DIR}"
ENV="${INSTALL_DIR}/.env.server"
touch "${ENV}"

# Payee satırını güncelle
if grep -q '^OAM_X402_PAYEE_ADDRESS=' "${ENV}"; then
  sed -i "s|^OAM_X402_PAYEE_ADDRESS=.*|OAM_X402_PAYEE_ADDRESS=${WALLET}|" "${ENV}"
else
  echo "OAM_X402_PAYEE_ADDRESS=${WALLET}" >> "${ENV}"
fi

# deployment stub — deployer alanı
mkdir -p deployments
if [[ -f deployments/sepolia.json ]]; then
  python3 - <<PY
import json
from pathlib import Path
p = Path("deployments/sepolia.json")
data = json.loads(p.read_text())
data["deployer"] = "${WALLET}"
data["x402_payee"] = "${WALLET}"
p.write_text(json.dumps(data, indent=2) + "\n")
print("  deployments/sepolia.json deployer güncellendi")
PY
else
  cp deployments/sepolia.example.json deployments/sepolia.json
  sed -i "s/0xYOUR_DEPLOYER/${WALLET}/" deployments/sepolia.json
  sed -i "s/0xYOUR_TREASURY_WALLET/${WALLET}/" deployments/sepolia.json
fi

# Opsiyonel: private key bu cüzdana aitse .funding.key olarak kaydet
if [[ -n "${DEPLOYER_PRIVATE_KEY:-}" ]]; then
  ADDR="$(node -e "const {Wallet}=require('ethers'); console.log(new Wallet(process.env.DEPLOYER_PRIVATE_KEY).address)")"
  if [[ "${ADDR,,}" != "${WALLET,,}" ]]; then
    echo "  ⚠ DEPLOYER_PRIVATE_KEY adresi eşleşmiyor: ${ADDR} != ${WALLET}"
  else
    echo "${DEPLOYER_PRIVATE_KEY}" > "${INSTALL_DIR}/.funding.key"
    chmod 600 "${INSTALL_DIR}/.funding.key"
    echo "  ✓ .funding.key kaydedildi — enable_base_sepolia.sh deploy edebilir"
  fi
fi

echo ""
echo "  Fonlama cüzdanı: ${WALLET}"
WALLET="${WALLET}" python3 - <<'PY'
import json, os, urllib.request
addr = os.environ["WALLET"]
def bal(rpc):
    req = urllib.request.Request(rpc, data=json.dumps({"jsonrpc":"2.0","method":"eth_getBalance","params":[addr,"latest"],"id":1}).encode(), headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=12) as r:
        return int(json.load(r)["result"], 16) / 1e18
for label, rpc in [("Base Sepolia", "https://sepolia.base.org"), ("Ethereum Sepolia", "https://sepolia.drpc.org")]:
    try:
        print(f"  {label}: {bal(rpc):.6f} ETH")
    except Exception as e:
        print(f"  {label}: ? ({e})")
PY

echo ""
echo "  Base Sepolia ETH yoksa: https://testnets.superbridge.app/base-sepolia"
echo "  veya aynı adrese Base Sepolia faucet."
echo ""
echo "  Private key sunucuya verildiyse:"
echo "  DEPLOYER_PRIVATE_KEY=0x... bash scripts/set_funding_wallet.sh ${WALLET}"
echo "  bash scripts/enable_base_sepolia.sh"
echo ""

if systemctl is-active --quiet oam-ecosystem 2>/dev/null; then
  systemctl restart oam-ecosystem
  echo "  ✓ oam-ecosystem yeniden başlatıldı"
fi
