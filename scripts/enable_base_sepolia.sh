#!/usr/bin/env bash
# Base Sepolia (84532) — Axium on-chain bağlantı + staking deploy
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/fizobia}"
cd "${INSTALL_DIR}"

echo ""
echo "  Axium — Base Sepolia On-Chain"
echo ""

if [[ "$(id -u)" -ne 0 ]]; then
  echo "  root olarak çalıştırın"
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive

if ! command -v node >/dev/null 2>&1; then
  echo "  Node.js kuruluyor…"
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y -qq nodejs
fi

echo "  node $(node -v) · npm $(npm -v)"

if [[ ! -d node_modules ]]; then
  echo "  npm install…"
  npm install --silent
fi

KEY_FILE="${INSTALL_DIR}/.deployer.key"
if [[ -z "${DEPLOYER_PRIVATE_KEY:-}" ]]; then
  if [[ -f "${KEY_FILE}" ]]; then
    DEPLOYER_PRIVATE_KEY="$(cat "${KEY_FILE}")"
  else
    DEPLOYER_PRIVATE_KEY="$(node -e "const {Wallet}=require('ethers'); const w=Wallet.createRandom(); console.log(w.privateKey)")"
    echo "${DEPLOYER_PRIVATE_KEY}" > "${KEY_FILE}"
    chmod 600 "${KEY_FILE}"
    DEPLOY_ADDR="$(node -e "const {Wallet}=require('ethers'); console.log(new Wallet('${DEPLOYER_PRIVATE_KEY}').address)")"
    echo ""
    echo "  Yeni deployer cüzdan: ${DEPLOY_ADDR}"
    echo "  Base Sepolia ETH gerekli (0.002 ETH yeterli):"
    echo "  https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet"
    echo ""
  fi
fi

export DEPLOYER_PRIVATE_KEY
DEPLOY_ADDR="$(node -e "const {Wallet}=require('ethers'); console.log(new Wallet(process.env.DEPLOYER_PRIVATE_KEY).address)")"
BAL_WEI="$(curl -sS -X POST https://sepolia.base.org -H 'Content-Type: application/json' \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"eth_getBalance\",\"params\":[\"${DEPLOY_ADDR}\",\"latest\"],\"id\":1}" \
  | python3 -c "import sys,json; print(int(json.load(sys.stdin)['result'],16))")"
BAL_ETH="$(python3 -c "print(${BAL_WEI}/1e18)")"
echo "  Deployer: ${DEPLOY_ADDR} · bakiye: ${BAL_ETH} ETH"

if python3 -c "exit(0 if ${BAL_WEI} > 0 else 1)"; then
  echo "  Sözleşmeler deploy ediliyor…"
  npm run compile
  npm run deploy:sepolia
else
  echo ""
  echo "  ⚠ Bakiye yok — RPC modu açılıyor (cüzdan bağlantısı + mesh on-chain)."
  echo "  ETH yükledikten sonra tekrar çalıştırın: bash scripts/enable_base_sepolia.sh"
  if [[ ! -f deployments/sepolia.json ]]; then
    cp deployments/sepolia.example.json deployments/sepolia.json
    sed -i "s/0xYOUR_DEPLOYER/${DEPLOY_ADDR}/" deployments/sepolia.json
    sed -i "s/0xYOUR_TREASURY_WALLET/${DEPLOY_ADDR}/" deployments/sepolia.json
  fi
fi

# .env.server on-chain blok
ENV="${INSTALL_DIR}/.env.server"
touch "${ENV}"
grep -v '^OAM_ONCHAIN_\|^OAM_X402_DEV\|^OAM_X402_RPC\|^OAM_X402_CHAIN\|^OAM_X402_PAYEE\|^OAM_X402_NETWORK' "${ENV}" > "${ENV}.tmp" || true
mv "${ENV}.tmp" "${ENV}"

cat >> "${ENV}" <<EOF

# Base Sepolia on-chain
OAM_ONCHAIN_ENABLED=true
OAM_ONCHAIN_REQUIRE_TX=false
OAM_ONCHAIN_CHAIN_ID=84532
OAM_ONCHAIN_RPC_URL=https://sepolia.base.org
OAM_ONCHAIN_DEPLOYMENT=deployments/sepolia.json
OAM_X402_NETWORK=base-sepolia
OAM_X402_RPC_URL=https://sepolia.base.org
OAM_X402_CHAIN_ID=84532
OAM_X402_USDC_CONTRACT=0x036CbD53842c5426634e7929541eC2318f3dCF7e
OAM_X402_PAYEE_ADDRESS=${DEPLOY_ADDR}
OAM_X402_DEV_ACCEPT_PROOF=true
EOF

if [[ -f deployments/sepolia.json ]] && grep -q '"factory":' deployments/sepolia.json && ! grep -q '"factory": ""' deployments/sepolia.json; then
  sed -i 's/^OAM_ONCHAIN_REQUIRE_TX=.*/OAM_ONCHAIN_REQUIRE_TX=true/' "${ENV}" 2>/dev/null || true
  echo "OAM_ONCHAIN_REQUIRE_TX=true" >> "${ENV}"
  echo "  ✓ Staking sözleşmeleri hazır — MetaMask stake aktif"
else
  echo "  ○ RPC bağlı — factory deploy sonrası stake açılır"
fi

systemctl restart oam-ecosystem
sleep 10

python3 -c "
import json, urllib.request
r=urllib.request.urlopen('http://127.0.0.1:8787/hub/onchain/config', timeout=10)
d=json.loads(r.read())
print('  onchain enabled:', d.get('enabled'), '| ready:', d.get('ready'))
print('  chain:', d.get('chain_name'), d.get('chain_id'))
print('  pools:', len(d.get('pools') or {}))
"

echo ""
echo "  Hub: https://axium.com.tr/hub"
echo "  MetaMask: Base Sepolia (84532) ağına geç"
echo ""
