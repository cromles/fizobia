#!/usr/bin/env bash
# Sunucuya geçmeden önce tam doğrulama
set -euo pipefail
cd "$(dirname "$0")/.."

echo ""
echo "  OAM Hub — Pre-Server Check"
echo ""

echo "[1/5] Unit & integration tests…"
python3 -m pytest -q --tb=no
echo "  ✓ tests OK"

echo "[2/5] Hub HTML render…"
python3 -c "
from app.api.hub_ui.render import render_hub_dashboard
from app.investment.hub import InvestmentHub
h = InvestmentHub()
html = render_hub_dashboard([], h.split, demo_mode=False)
assert 'synapsePrompt' in html or 'userPrompt' in html
assert 'mesh-proof-hero' in html or 'meshProofHero' in html
assert 'featured-worker' in html
assert 'dialogueThread' in html
assert 'agentDialoguePanel' in html
print('  ✓ UI render OK')
"

echo "[3/5] x402 + mesh proof + departman imports…"
python3 -c "
from app.mesh.proof_pipeline import run_mesh_proof_pipeline
from app.mesh.arena_pipeline import run_arena_pipeline
from app.mesh.article_pipeline import run_article_pipeline
from app.mesh.departments import list_departments, DEPARTMENT_COPYWRITING
from app.mesh.synapse_manifest import get_synapse_manifest
from app.investment.x402_gateway import list_x402_services, arena_price_usd
from app.mesh.ecosystem_registry import ECOSYSTEM_STACK_AGENT_IDS
assert len(list_x402_services()['services']) >= 3
assert arena_price_usd() > 0
assert get_synapse_manifest()['code'] == 'THE_SYNAPSE_NET'
assert list_departments()['count'] == 3
assert len(ECOSYSTEM_STACK_AGENT_IDS) == 18
print('  ✓ x402 + arena + departmanlar OK')
"

echo "[4/5] On-chain config…"
python3 -c "
from pathlib import Path
assert Path('scripts/deploy_base_sepolia.sh').exists()
assert Path('.env.onchain.example').exists()
print('  ✓ on-chain deploy scripts OK')
"

echo "[5/5] Demo scripts (syntax)…"
python3 -m py_compile scripts/demo_mesh_proof.py scripts/demo_x402_all.py scripts/demo_departments_simulation.py
chmod +x scripts/ready_for_server.sh scripts/go_live.sh
echo "  ✓ demo scripts OK"

echo ""
echo "  Hazır — sunucuya deploy edilebilir."
echo "  Lokal demo: bash scripts/go_live.sh"
echo "  Simülasyon: PYTHONPATH=. python3 scripts/demo_departments_simulation.py"
echo "  Sunucu:     bash scripts/ready_for_server.sh"
echo ""
