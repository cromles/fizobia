"""DeFi TVL — DefiLlama (anahtarsız)."""

from __future__ import annotations

from typing import Any, Dict, List

import httpx

AGENT_ID = "oam.analyst.defi.local"
DISPLAY_NAME = "DeFi-Pulse"

_DEFILLAMA_CHAINS = "https://api.llama.fi/v2/chains"


def _top_chains(rows: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    ranked = sorted(rows, key=lambda r: float(r.get("tvl") or 0), reverse=True)
    top: List[Dict[str, Any]] = []
    for row in ranked[:limit]:
        tvl = float(row.get("tvl") or 0)
        top.append(
            {
                "name": row.get("name") or row.get("tokenSymbol") or "unknown",
                "symbol": row.get("tokenSymbol"),
                "tvl_usd": round(tvl, 2),
                "gecko_id": row.get("gecko_id"),
            }
        )
    return top


def fetch_defi_snapshot(*, limit: int = 8) -> Dict[str, Any]:
    """Zincir bazlı toplam kilitli değer (TVL) — DefiLlama."""
    cap = max(3, min(int(limit), 20))
    with httpx.Client(timeout=15.0) as client:
        response = client.get(_DEFILLAMA_CHAINS)
        response.raise_for_status()
        rows = response.json()

    if not isinstance(rows, list):
        raise ValueError("DefiLlama beklenmeyen yanıt")

    top = _top_chains(rows, cap)
    total_tvl = sum(c["tvl_usd"] for c in top)
    leader = top[0] if top else {}
    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "chains_shown": len(top),
        "total_tvl_top_usd": round(total_tvl, 2),
        "leader_chain": leader.get("name"),
        "leader_tvl_usd": leader.get("tvl_usd"),
        "top_chains": top,
        "analysis": (
            f"DeFi TVL lideri {leader.get('name', '—')} "
            f"${leader.get('tvl_usd', 0):,.0f} · ilk {len(top)} zincir"
        ),
        "source": "defillama",
        "real_data": True,
    }


async def fetch_defi_snapshot_async(*, limit: int = 8) -> Dict[str, Any]:
    cap = max(3, min(int(limit), 20))
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(_DEFILLAMA_CHAINS)
        response.raise_for_status()
        rows = response.json()

    if not isinstance(rows, list):
        raise ValueError("DefiLlama beklenmeyen yanıt")

    top = _top_chains(rows, cap)
    total_tvl = sum(c["tvl_usd"] for c in top)
    leader = top[0] if top else {}
    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "chains_shown": len(top),
        "total_tvl_top_usd": round(total_tvl, 2),
        "leader_chain": leader.get("name"),
        "leader_tvl_usd": leader.get("tvl_usd"),
        "top_chains": top,
        "analysis": (
            f"DeFi TVL lideri {leader.get('name', '—')} "
            f"${leader.get('tvl_usd', 0):,.0f} · ilk {len(top)} zincir"
        ),
        "source": "defillama",
        "real_data": True,
    }
