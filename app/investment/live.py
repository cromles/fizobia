from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, List, Tuple

import httpx

from app.config import settings
from app.investment.hub import InvestmentHub
from app.protocol.schemas import AgentManifest


def count_reachable_agents(agents: List[AgentManifest]) -> int:
    return sum(1 for manifest in agents if _probe_endpoint(manifest.endpoint)[0])


def _tasks_per_minute(events: List[Any], window_seconds: float = 3600.0) -> float:
    cutoff = time.time() - window_seconds
    recent = [
        event
        for event in events
        if event.created_at and event.created_at.timestamp() >= cutoff
    ]
    if not recent:
        return 0.0
    span = max(60.0, time.time() - min(event.created_at.timestamp() for event in recent))
    return round((len(recent) / span) * 60.0, 2)


def _probe_endpoint(endpoint: str) -> Tuple[bool, float]:
    if not endpoint or not endpoint.startswith("http"):
        return False, 0.0
    url = f"{endpoint.rstrip('/')}/health"
    try:
        start = time.perf_counter()
        with httpx.Client(timeout=2.0) as client:
            response = client.get(url)
        latency_ms = (time.perf_counter() - start) * 1000
        return response.status_code == 200, latency_ms
    except Exception:
        return False, 0.0


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
    reachable_count = count_reachable_agents(agents)
    for card in cards:
        manifest = next((m for m in agents if m.agent_id == card.profile.agent_id), None)
        endpoint = manifest.endpoint if manifest else ""
        reachable, probe_latency = _probe_endpoint(endpoint)

        if reachable:
            status = "active"
            latency_ms = round(probe_latency, 1)
        elif card.health.total_calls > 0:
            status = "offline"
            latency_ms = card.health.avg_latency_ms
        else:
            status = "standby"
            latency_ms = 0.0

        agent_rows.append(
            {
                "agent_id": card.profile.agent_id,
                "display_name": card.profile.display_name,
                "token_symbol": card.profile.token_symbol,
                "agent_class": card.profile.agent_class.value,
                "status": status,
                "reachable": reachable,
                "success_rate": card.health.success_rate,
                "latency_ms": latency_ms,
                "total_calls": card.health.total_calls,
                "apy": card.finance.estimated_apy,
                "tvl": card.finance.staking_pool_tvl_usd,
                "revenue_24h": card.finance.volume_24h_usd,
                "endpoint": endpoint,
            }
        )

    feed: List[Dict[str, Any]] = []
    name_by_id = {c.profile.agent_id: c.profile.display_name for c in cards}
    for event in reversed(events[-20:]):
        is_demo = event.task_id.startswith("demo_")
        worker_name = name_by_id.get(event.agent_id, event.agent_id)
        source_label = {
            "mesh_task": "görev",
            "x402": "x402 ödeme",
            "external": "harici gelir",
        }.get(event.source.value if hasattr(event.source, "value") else str(event.source), "gelir")
        feed.append(
            {
                "type": "revenue",
                "agent_id": event.agent_id,
                "worker_name": worker_name,
                "task_id": event.task_id,
                "gross_usd": event.gross_usd,
                "staking_usd": event.staking_usd,
                "success": event.success,
                "latency_ms": event.latency_ms,
                "tx_hash": event.tx_hash,
                "source": event.source.value if hasattr(event.source, "value") else str(event.source),
                "time": event.created_at.isoformat() if event.created_at else "",
                "simulated": is_demo,
                "message": (
                    f"{worker_name} · {source_label} · ${event.gross_usd:.4f} gelir (sizin payınız havuza aktı)"
                    if event.success and not is_demo
                    else (
                        f"{worker_name} görev denedi (başarısız)"
                        if not is_demo
                        else f"{worker_name} · demo kayıt"
                    )
                ),
            }
        )

    real_events = [e for e in feed if not e.get("simulated")]
    mesh_offline = reachable_count == 0 and not settings.hub_demo_mode
    tasks_per_min = _tasks_per_minute(events)

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "demo_mode": settings.hub_demo_mode,
        "data_notice": (
            "Metrikler ve geçmiş işlemler DEMO verisidir. "
            "Gerçek mod için OAM_HUB_DEMO=false ve python -m app.run_stack kullanın."
            if settings.hub_demo_mode
            else (
                "Her kayıt gerçek ajan faaliyetinden gelir — dijital işçileriniz "
                "ağda görev alır, çalışır ve kazancın %65'i staking havuzuna aktarılır. "
                "Pasif ortaklık: siz çalıştırmazsınız, mesh 7/24 çalışır."
            )
        ),
        "network": {
            "status": "online" if reachable_count > 0 else "degraded",
            "protocol": "OAM-NAT-v2",
            "mesh_offline": mesh_offline,
            "setup_command": "python3 -m app.run_stack",
            "reachable_agents": reachable_count,
            "active_agents": len([a for a in agent_rows if a["status"] == "active"]),
            "total_agents": len(agent_rows),
            "total_tvl_usd": round(total_tvl, 2),
            "total_revenue_usd": round(total_revenue, 4),
            "total_calls": total_calls,
            "tasks_per_min": tasks_per_min,
            "real_event_count": len(real_events),
        },
        "agents": agent_rows,
        "activity_feed": feed,
    }
