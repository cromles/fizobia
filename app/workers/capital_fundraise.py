from __future__ import annotations

import asyncio
from typing import Any, Dict

AGENT_ID = "oam.capital.fundraise.local"
DISPLAY_NAME = "Fund-Radar"


def scan_fundraise_signals(
    *,
    total_revenue_usd: float = 0.0,
    mesh_proofs: int = 0,
    total_agents: int = 0,
    tvl_usd: float = 0.0,
) -> Dict[str, Any]:
    """Gelir, kanıt ve stake sinyalleri — sermaye radarı."""
    readiness = "bootstrap"
    if mesh_proofs >= 3 and total_revenue_usd > 0:
        readiness = "early_revenue"
    if tvl_usd > 100:
        readiness = "staking_signal"
    if mesh_proofs >= 10 and total_revenue_usd > 50:
        readiness = "fundraise_ready"

    return {
        "agent_id": AGENT_ID,
        "display_name": DISPLAY_NAME,
        "readiness": readiness,
        "signals": {
            "mesh_proofs": mesh_proofs,
            "revenue_usd": round(total_revenue_usd, 2),
            "tvl_usd": round(tvl_usd, 2),
            "agents": total_agents,
        },
        "recommendation": (
            "Mesh proof + x402 ile mikro-gelir üret; stake TVL büyüdükçe pasif sermaye sinyali güçlenir."
        ),
        "real_data": True,
    }


async def scan_fundraise_signals_async(**kwargs: Any) -> Dict[str, Any]:
    return await asyncio.to_thread(scan_fundraise_signals, **kwargs)
