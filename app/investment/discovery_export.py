from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.config import settings
from app.investment.hub import InvestmentHub
from app.protocol.schemas import AgentManifest


def build_platform_agent_card() -> Dict[str, Any]:
    """A2A / x402 Bazaar uyumlu platform kimlik kartı."""
    base = settings.public_base_url.rstrip("/")
    return {
        "name": "OAM Hub",
        "description": (
            "Pasif dijital işçi ortaklığı platformu — USDC stake, gerçek görev geliri, "
            "%65 staking havuzu payı. Mesh orchestrator 7/24 çalışır; yatırımcı agent çalıştırmaz."
        ),
        "url": base,
        "version": "1.0",
        "protocols": ["OAM", "x402", "A2A", "MPP"],
        "payment": {
            "protocol": "x402",
            "assets": ["USDC"],
            "webhook": f"{base}/hub/revenue/x402",
            "facilitator": "coinbase-x402",
        },
        "discovery": {
            "catalog": f"{base}/hub/discovery",
            "sdk": f"{base}/hub/sdk/config",
            "live": f"{base}/hub/live",
        },
        "capabilities": [
            "passive_partnership_staking",
            "revenue_linked_rewards",
            "live_worker_mesh",
            "on_chain_staking",
        ],
    }


def build_mpp_descriptor() -> Dict[str, Any]:
    """Machine Payments Protocol tanımlayıcısı."""
    base = settings.public_base_url.rstrip("/")
    return {
        "protocol": "MPP",
        "version": "1.0",
        "platform": "OAM-Hub",
        "base_url": base,
        "payment_methods": [
            {
                "type": "x402",
                "assets": ["USDC"],
                "settlement": "instant",
                "webhook": f"{base}/hub/revenue/x402",
            },
            {
                "type": "on_chain_stake",
                "assets": ["USDC"],
                "endpoint": f"{base}/hub/stake",
            },
        ],
        "agent_catalog": f"{base}/hub/discovery",
        "operator_console": f"{base}/hub",
    }


def build_agent_discovery_entry(
    manifest: AgentManifest,
    card: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    profile = (card or {}).get("profile", {})
    finance = (card or {}).get("finance", {})
    health = (card or {}).get("health", {})
    pool = (card or {}).get("pool", {})
    caps = [
        {
            "name": c.name,
            "description": c.description,
            "input_schema": c.input_schema,
            "output_schema": c.output_schema,
        }
        for c in manifest.capabilities
    ]
    base = settings.public_base_url.rstrip("/")
    return {
        "agent_id": manifest.agent_id,
        "display_name": profile.get("display_name", manifest.agent_id),
        "agent_class": profile.get("agent_class"),
        "endpoint": manifest.endpoint,
        "capabilities": caps,
        "partnership_mode": profile.get("partnership_mode", "passive"),
        "pricing": {
            "cost_per_1k_tokens_usd": manifest.cost_per_token,
            "revenue_split": {
                "staking": 0.65,
                "platform": 0.10,
                "operator": 0.25,
            },
        },
        "finance": {
            "apy_pct": finance.get("estimated_apy", 0),
            "tvl_usd": finance.get("staking_pool_tvl_usd", 0),
            "volume_24h_usd": finance.get("volume_24h_usd", 0),
        },
        "health": {
            "success_rate": health.get("success_rate", 1.0),
            "total_calls": health.get("total_calls", 0),
        },
        "staking": {
            "token_symbol": pool.get("token_symbol"),
            "pool_contract": pool.get("contract_address"),
            "stake_url": f"{base}/hub/partnership/stake",
            "hub_card_url": f"{base}/hub/agents/{manifest.agent_id}",
        },
        "x402": {
            "accepts_payment": True,
            "webhook_route": f"{base}/hub/revenue/x402",
            "asset": "USDC",
        },
    }


def build_discovery_catalog(
    hub: InvestmentHub,
    agents: List[AgentManifest],
) -> Dict[str, Any]:
    cards = {c.profile.agent_id: c.model_dump() for c in hub.list_identity_cards(agents)}
    entries = [
        build_agent_discovery_entry(m, cards.get(m.agent_id))
        for m in agents
    ]
    base = settings.public_base_url.rstrip("/")
    return {
        "protocol": "OAM-Hub-Discovery",
        "version": "1.0",
        "platform": build_platform_agent_card(),
        "agent_count": len(entries),
        "agents": entries,
        "endpoints": {
            "stake_passive": f"{base}/hub/partnership/stake",
            "x402_revenue": f"{base}/hub/revenue/x402",
            "live_feed": f"{base}/hub/live",
            "well_known": f"{base}/.well-known/agent.json",
        },
        "positioning": {
            "vs_virtuals": "Gelir = iş çıktısı, token spekülasyonu değil",
            "vs_olas": "Pasif ortaklık — agent'ı siz çalıştırmazsınız",
            "vs_marketplaces": "Yatırımcı katmanı + gelir havuzu",
        },
    }
