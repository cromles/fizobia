#!/usr/bin/env bash
# OAM on-chain stack: Hardhat node + deploy + gateway + ajanlar
set -euo pipefail
cd "$(dirname "$0")/.."

export OAM_HUB_DEMO=false
export OAM_ONCHAIN_ENABLED=true
export OAM_ONCHAIN_REQUIRE_TX=true
export OAM_ONCHAIN_OPERATOR_KEY="${OAM_ONCHAIN_OPERATOR_KEY:-0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80}"

echo "[1/4] Hardhat node başlatılıyor (8545)…"
npx hardhat node > /tmp/oam-hardhat.log 2>&1 &
HARDHAT_PID=$!
sleep 3

echo "[2/4] Sözleşmeler deploy ediliyor…"
npm run deploy:local

echo "[3/4] Operatöre USDC mint (opsiyonel)…"
# deployer zaten 1M USDC alır — Hardhat account #0

echo "[4/4] OAM stack başlatılıyor…"
python3 -m app.run_stack &
STACK_PID=$!

echo ""
echo "  The Hub:  http://127.0.0.1:8787/hub"
echo "  On-chain: http://127.0.0.1:8787/hub/onchain/config"
echo "  Hardhat:  http://127.0.0.1:8545 (chain 31337)"
echo "  MetaMask: Hardhat Local ağı ekleyin, Account #0 private key ile test USDC"
echo ""
echo "Durdurmak için: kill $HARDHAT_PID $STACK_PID"

wait $STACK_PID
