"""Döviz kurları — Frankfurter (ECB, anahtarsız)."""

from __future__ import annotations

from typing import Any, Dict, List

import httpx

AGENT_ID = "oam.analyst.fx.local"
DISPLAY_NAME = "FX-Pulse"

_FRANKFURTER = "https://api.frankfurter.app/latest"


def _parse_symbols(raw: str) -> List[str]:
    parts = [p.strip().upper() for p in (raw or "TRY,EUR").split(",") if p.strip()]
    return parts or ["TRY", "EUR"]


def fetch_fx_snapshot(*, base: str = "USD", symbols: str = "TRY,EUR") -> Dict[str, Any]:
    """USD bazlı güncel kurlar — Frankfurter API."""
    base_ccy = (base or "USD").strip().upper()
    target_syms = _parse_symbols(symbols)
    params = {"from": base_ccy, "to": ",".join(target_syms)}
    with httpx.Client(timeout=12.0) as client:
        response = client.get(_FRANKFURTER, params=params)
        response.raise_for_status()
        payload = response.json()

    rates = {k.upper(): float(v) for k, v in (payload.get("rates") or {}).items()}
    try_rate = rates.get("TRY")
    analysis_parts = [f"{base_ccy}/{sym}: {rates[sym]:,.4f}" for sym in target_syms if sym in rates]
    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "base": base_ccy,
        "date": payload.get("date"),
        "rates": rates,
        "usd_try": try_rate,
        "analysis": " · ".join(analysis_parts) if analysis_parts else "Kur verisi alındı",
        "source": "frankfurter.app",
        "real_data": True,
    }


async def fetch_fx_snapshot_async(*, base: str = "USD", symbols: str = "TRY,EUR") -> Dict[str, Any]:
    base_ccy = (base or "USD").strip().upper()
    target_syms = _parse_symbols(symbols)
    params = {"from": base_ccy, "to": ",".join(target_syms)}
    async with httpx.AsyncClient(timeout=12.0) as client:
        response = await client.get(_FRANKFURTER, params=params)
        response.raise_for_status()
        payload = response.json()

    rates = {k.upper(): float(v) for k, v in (payload.get("rates") or {}).items()}
    try_rate = rates.get("TRY")
    analysis_parts = [f"{base_ccy}/{sym}: {rates[sym]:,.4f}" for sym in target_syms if sym in rates]
    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "base": base_ccy,
        "date": payload.get("date"),
        "rates": rates,
        "usd_try": try_rate,
        "analysis": " · ".join(analysis_parts) if analysis_parts else "Kur verisi alındı",
        "source": "frankfurter.app",
        "real_data": True,
    }
