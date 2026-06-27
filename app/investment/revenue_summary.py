from __future__ import annotations

from typing import Any, Dict, List

from app.config import settings
from app.investment.hub import InvestmentHub
from app.investment.onchain import build_public_config
from app.mesh.agent_catalog import (
    AGENT_API_TAG,
    REVENUE_CORE_AGENT_IDS,
    agent_label,
    is_mesh_proof_agent,
)
from app.mesh.proof_vault import get_proof_vault
from app.protocol.schemas import AgentManifest


def _stake_mode_label(stake_mode: str, onchain: Dict[str, Any]) -> str:
    if stake_mode == "onchain":
        return "Zincir stake aktif — MetaMask ile gerçek havuz"
    funding = onchain.get("funding") or {}
    if funding.get("bridge_needed"):
        eth_sep = funding.get("ethereum_sepolia_eth") or 0
        return (
            f"Demo defter — payee cüzdanda Ethereum Sepolia'da {eth_sep:.4f} ETH var; "
            "Base Sepolia köprüsü gerekli"
        )
    chain = onchain.get("chain_name", "Base Sepolia")
    if onchain.get("connected"):
        return f"Demo defter — gelir gerçek, stake uygulama içi ({chain} RPC hazır)"
    return "Demo defter — gelir gerçek, stake uygulama içi (zincir yapılandırılıyor)"


def build_revenue_summary(
    hub: InvestmentHub,
    manifests: List[AgentManifest],
) -> Dict[str, Any]:
    """Pasif ortaklık döngüsü — kanıt, x402 geliri ve stake durumu."""
    vault_stats = get_proof_vault().stats()
    onchain = build_public_config()
    stake_mode = str(onchain.get("stake_mode", "ledger_demo"))

    cards = hub.list_identity_cards(manifests)
    card_map = {c.profile.agent_id: c for c in cards}

    agents_summary: List[Dict[str, Any]] = []
    total_x402 = 0.0
    total_staking = 0.0
    total_tvl = 0.0

    for agent_id in REVENUE_CORE_AGENT_IDS:
        card = card_map.get(agent_id)
        if card is None:
            continue
        x402_rev = hub.revenue.external_revenue_total(agent_id)
        staking_rev = hub.revenue.staking_revenue(agent_id)
        total_x402 += x402_rev
        total_staking += staking_rev
        total_tvl += card.finance.staking_pool_tvl_usd
        agents_summary.append(
            {
                "agent_id": agent_id,
                "display_name": agent_label(agent_id),
                "api_tag": AGENT_API_TAG.get(agent_id, ""),
                "mesh_proof": is_mesh_proof_agent(agent_id),
                "total_revenue_usd": round(hub.revenue.total_revenue(agent_id), 4),
                "x402_revenue_usd": round(x402_rev, 4),
                "staking_to_pool_usd": round(staking_rev, 4),
                "tvl_usd": round(card.finance.staking_pool_tvl_usd, 2),
                "apy_pct": card.finance.estimated_apy,
            }
        )

    return {
        "mission": "Pasif ortaklık — mesh 7/24 çalışır, görev gelirinin %65'i stake edenlere.",
        "revenue_core_count": len(REVENUE_CORE_AGENT_IDS),
        "stake_mode": stake_mode,
        "stake_mode_label": _stake_mode_label(stake_mode, onchain),
        "split": hub.split.model_dump(),
        "totals": {
            "x402_revenue_usd": round(total_x402, 4),
            "staking_pool_usd": round(total_staking, 4),
            "tvl_usd": round(total_tvl, 2),
            "mesh_proofs": int(vault_stats.get("proofs_recorded", 0)),
        },
        "agents": agents_summary,
        "mesh_proof": {
            "cta_path": "/hub/proof/mesh/run",
            "price_usd": settings.x402_mesh_proof_price_usd,
            "workers": ["Web-Crawler", "Sentiment", "Market", "On-Chain"],
            "real_data": True,
        },
        "onchain": {
            "enabled": onchain.get("enabled"),
            "connected": onchain.get("connected"),
            "ready": onchain.get("ready"),
            "chain_name": onchain.get("chain_name"),
            "pool_count": len(onchain.get("pools") or {}),
            "deployer": onchain.get("deployer"),
            "deployer_balance_eth": onchain.get("deployer_balance_eth"),
            "deploy_ready": onchain.get("deploy_ready", False),
            "faucet_url": "https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet",
        },
        "demo_mode": settings.hub_demo_mode,
    }
