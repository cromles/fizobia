#!/usr/bin/env bash
# Base Sepolia — StakingFactory + ajan havuzları deploy
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ -z "${DEPLOYER_PRIVATE_KEY:-}" ]]; then
  echo "DEPLOYER_PRIVATE_KEY gerekli (Base Sepolia ETH olan cüzdan)"
  echo "Örnek: DEPLOYER_PRIVATE_KEY=0x... bash scripts/deploy_base_sepolia.sh"
  exit 1
fi

echo "[1/3] npm bağımlılıkları…"
npm install --silent

echo "[2/3] Sözleşmeler derleniyor…"
npm run compile

echo "[3/3] Base Sepolia deploy…"
npm run deploy:sepolia

echo ""
echo "Tamam — deployments/sepolia.json oluşturuldu."
echo "Sunucuda: cat .env.onchain.example >> .env.server  (değerleri düzenleyin)"
echo "MetaMask: Base Sepolia ağı (chain 84532) + test USDC"
