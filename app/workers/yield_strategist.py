"""Getiri stratejisti — DeFiLlama yield havuzları, TVL + APY taraması."""

from __future__ import annotations

from typing import Any, Dict, List

import httpx

AGENT_ID = "oam.expert.yield.local"
DISPLAY_NAME = "Yield-Strategist"

_YIELDS_API = "https://yields.llama.fi/pools"
_STABLE_HINTS = ("USDC", "USDT", "DAI", "FRAX", "LUSD", "USD")


def _is_stable_pool(symbol: str) -> bool:
    sym = (symbol or "").upper()
    return any(hint in sym for hint in _STABLE_HINTS)


def _top_yield_pools(rows: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    eligible: List[Dict[str, Any]] = []
    for row in rows:
        tvl = float(row.get("tvlUsd") or 0)
        apy = float(row.get("apy") or 0)
        symbol = str(row.get("symbol") or "")
        if tvl < 5_000_000 or apy <= 0 or apy > 25:
            continue
        if not _is_stable_pool(symbol):
            continue
        eligible.append(row)

    ranked = sorted(eligible, key=lambda r: float(r.get("apy") or 0), reverse=True)
    out: List[Dict[str, Any]] = []
    for row in ranked[:limit]:
        out.append(
            {
                "project": row.get("project") or "—",
                "chain": row.get("chain") or "—",
                "symbol": row.get("symbol") or "—",
                "apy_pct": round(float(row.get("apy") or 0), 2),
                "tvl_usd": round(float(row.get("tvlUsd") or 0), 0),
            }
        )
    return out


def fetch_yield_snapshot(*, limit: int = 6) -> Dict[str, Any]:
    """Stabilcoin odaklı yüksek TVL yield havuzları — DefiLlama."""
    cap = max(3, min(int(limit), 12))
    with httpx.Client(timeout=20.0) as client:
        response = client.get(_YIELDS_API)
        response.raise_for_status()
        payload = response.json()

    rows = payload.get("data") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("DeFiLlama yields beklenmeyen yanıt")

    pools = _top_yield_pools(rows, cap)
    leader = pools[0] if pools else {}
    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "pools_scanned": len(rows),
        "items": pools,
        "count": len(pools),
        "leader_project": leader.get("project"),
        "leader_apy_pct": leader.get("apy_pct"),
        "leader_tvl_usd": leader.get("tvl_usd"),
        "analysis": (
            f"Yield: {leader.get('project', '—')} {leader.get('symbol', '')} "
            f"%{leader.get('apy_pct', 0)} APY · TVL ${leader.get('tvl_usd', 0):,.0f}"
            if leader
            else "Uygun stabil yield havuzu bulunamadı"
        ),
        "source": "defillama-yields",
        "real_data": True,
    }


async def fetch_yield_snapshot_async(*, limit: int = 6) -> Dict[str, Any]:
    cap = max(3, min(int(limit), 12))
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(_YIELDS_API)
        response.raise_for_status()
        payload = response.json()

    rows = payload.get("data") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("DeFiLlama yields beklenmeyen yanıt")

    pools = _top_yield_pools(rows, cap)
    leader = pools[0] if pools else {}
    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "pools_scanned": len(rows),
        "items": pools,
        "count": len(pools),
        "leader_project": leader.get("project"),
        "leader_apy_pct": leader.get("apy_pct"),
        "leader_tvl_usd": leader.get("tvl_usd"),
        "analysis": (
            f"Yield: {leader.get('project', '—')} {leader.get('symbol', '')} "
            f"%{leader.get('apy_pct', 0)} APY · TVL ${leader.get('tvl_usd', 0):,.0f}"
            if leader
            else "Uygun stabil yield havuzu bulunamadı"
        ),
        "source": "defillama-yields",
        "real_data": True,
    }
