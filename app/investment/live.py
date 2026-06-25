from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from app.investment.hub import InvestmentHub
from app.protocol.schemas import AgentManifest


def build_live_snapshot(
    hub: InvestmentHub,
    agents: List[AgentManifest],
) -> Dict[str, Any]:
    cards = hub.list_identity_cards(agents)
    events = hub.revenue.list_events(limit=30)
    total_tvl = sum(c.finance.staking_pool_tvl_usd for c in cards)
    total_revenue = sum(c.finance.total_revenue_usd for c in cards)
    total_calls = sum(c.health.total_calls for c in cards)

    agent_rows: List[Dict[str, Any]] = []
    for card in cards:
        manifest = next((m for m in agents if m.agent_id == card.profile.agent_id), None)
        reliability = manifest.reliability_score if manifest else card.health.success_rate
        status = "active" if reliability >= 0.5 else "degraded"
        if card.health.total_calls == 0:
            status = "standby"
        agent_rows.append(
            {
                "agent_id": card.profile.agent_id,
                "display_name": card.profile.display_name,
                "token_symbol": card.profile.token_symbol,
                "agent_class": card.profile.agent_class.value,
                "status": status,
                "success_rate": card.health.success_rate,
                "latency_ms": card.health.avg_latency_ms,
                "total_calls": card.health.total_calls,
                "apy": card.finance.estimated_apy,
                "tvl": card.finance.staking_pool_tvl_usd,
                "revenue_24h": card.finance.volume_24h_usd,
                "endpoint": manifest.endpoint if manifest else "",
            }
        )

    feed: List[Dict[str, Any]] = []
    for event in reversed(events[-20:]):
        feed.append(
            {
                "type": "revenue",
                "agent_id": event.agent_id,
                "task_id": event.task_id,
                "gross_usd": event.gross_usd,
                "staking_usd": event.staking_usd,
                "success": event.success,
                "latency_ms": event.latency_ms,
                "tx_hash": event.tx_hash,
                "time": event.created_at.isoformat() if event.created_at else "",
            }
        )

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "network": {
            "status": "online",
            "protocol": "OAM-NAT-v2",
            "active_agents": len([a for a in agent_rows if a["status"] == "active"]),
            "total_agents": len(agent_rows),
            "total_tvl_usd": round(total_tvl, 2),
            "total_revenue_usd": round(total_revenue, 4),
            "total_calls": total_calls,
        },
        "agents": agent_rows,
        "activity_feed": feed,
    }
