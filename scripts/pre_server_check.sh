#!/usr/bin/env bash
# Sunucuya geçmeden önce tam doğrulama
set -euo pipefail
cd "$(dirname "$0")/.."

echo ""
echo "  OAM Hub — Pre-Server Check"
echo ""

echo "[1/4] Unit & integration tests…"
python3 -m pytest -q --tb=no
echo "  ✓ tests OK"

echo "[2/4] Hub HTML render…"
python3 -c "
from app.api.hub_ui.render import render_hub_dashboard
from app.investment.hub import InvestmentHub
h = InvestmentHub()
html = render_hub_dashboard([], h.split, demo_mode=False)
assert 'mesh-proof-hero' in html or 'meshProofHero' in html
assert 'featured-worker' in html
print('  ✓ UI render OK')
"

echo "[3/4] x402 + mesh proof imports…"
python3 -c "
from app.mesh.proof_pipeline import run_mesh_proof_pipeline
from app.investment.x402_gateway import list_x402_services
assert len(list_x402_services()['services']) >= 3
print('  ✓ x402 catalog OK')
"

echo "[4/4] Demo scripts (syntax)…"
python3 -m py_compile scripts/demo_mesh_proof.py scripts/demo_x402_all.py
echo "  ✓ demo scripts OK"

echo ""
echo "  Hazır — sunucuya deploy edilebilir."
echo "  Lokal demo: bash scripts/start_hub.sh && python3 scripts/demo_mesh_proof.py"
echo "  On-chain:   bash scripts/start_onchain_stack.sh"
echo ""
