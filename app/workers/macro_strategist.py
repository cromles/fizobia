"""Makro strateji — küresel piyasa ve döviz sepeti (CoinGecko + Frankfurter)."""

from __future__ import annotations

from typing import Any, Dict, List

import httpx

AGENT_ID = "oam.expert.macro.local"
DISPLAY_NAME = "Macro-Strategist"

_COINGECKO_GLOBAL = "https://api.coingecko.com/api/v3/global"
_FRANKFURTER = "https://api.frankfurter.dev/v1/latest"


def _fetch_global(client: httpx.Client) -> Dict[str, Any]:
    response = client.get(_COINGECKO_GLOBAL)
    response.raise_for_status()
    return response.json().get("data") or {}


def _fetch_fx_basket(client: httpx.Client) -> Dict[str, float]:
    params = {"from": "USD", "to": "TRY,EUR,GBP,JPY,CHF"}
    response = client.get(_FRANKFURTER, params=params)
    response.raise_for_status()
    rates = response.json().get("rates") or {}
    return {k.upper(): float(v) for k, v in rates.items()}


def fetch_macro_snapshot(*, fx_symbols: str = "TRY,EUR,GBP,JPY") -> Dict[str, Any]:
    """Küresel kripto makro + USD sepeti — portföy ve risk kararları için."""
    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        global_data = _fetch_global(client)
        rates = _fetch_fx_basket(client)

    mcap_pct = global_data.get("market_cap_change_percentage_24h_usd") or 0
    total_mcap = float((global_data.get("total_market_cap") or {}).get("usd") or 0)
    btc_dom = float((global_data.get("market_cap_percentage") or {}).get("btc") or 0)
    eth_dom = float((global_data.get("market_cap_percentage") or {}).get("eth") or 0)
    active_cryptos = int(global_data.get("active_cryptocurrencies") or 0)

    usd_try = rates.get("TRY")
    risk_tone = "risk-on" if mcap_pct > 1 else "risk-off" if mcap_pct < -1 else "nötr"

    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "total_market_cap_usd": round(total_mcap, 0),
        "market_change_24h_pct": round(float(mcap_pct), 2),
        "btc_dominance_pct": round(btc_dom, 2),
        "eth_dominance_pct": round(eth_dom, 2),
        "active_cryptocurrencies": active_cryptos,
        "usd_try": usd_try,
        "fx_basket": rates,
        "risk_tone": risk_tone,
        "analysis": (
            f"Makro: 24s {mcap_pct:+.1f}% · BTC dom %{btc_dom:.1f} · "
            f"USD/TRY {usd_try:,.2f}" if usd_try else f"Makro: 24s {mcap_pct:+.1f}% · BTC dom %{btc_dom:.1f}"
        ),
        "source": "coingecko+frankfurter",
        "real_data": True,
    }


async def fetch_macro_snapshot_async(*, fx_symbols: str = "TRY,EUR,GBP,JPY") -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        g_resp = await client.get(_COINGECKO_GLOBAL)
        g_resp.raise_for_status()
        global_data = g_resp.json().get("data") or {}

        params = {"from": "USD", "to": "TRY,EUR,GBP,JPY,CHF"}
        f_resp = await client.get(_FRANKFURTER, params=params)
        f_resp.raise_for_status()
        rates = {k.upper(): float(v) for k, v in (f_resp.json().get("rates") or {}).items()}

    mcap_pct = global_data.get("market_cap_change_percentage_24h_usd") or 0
    total_mcap = float((global_data.get("total_market_cap") or {}).get("usd") or 0)
    btc_dom = float((global_data.get("market_cap_percentage") or {}).get("btc") or 0)
    eth_dom = float((global_data.get("market_cap_percentage") or {}).get("eth") or 0)
    active_cryptos = int(global_data.get("active_cryptocurrencies") or 0)
    usd_try = rates.get("TRY")
    risk_tone = "risk-on" if mcap_pct > 1 else "risk-off" if mcap_pct < -1 else "nötr"

    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "total_market_cap_usd": round(total_mcap, 0),
        "market_change_24h_pct": round(float(mcap_pct), 2),
        "btc_dominance_pct": round(btc_dom, 2),
        "eth_dominance_pct": round(eth_dom, 2),
        "active_cryptocurrencies": active_cryptos,
        "usd_try": usd_try,
        "fx_basket": rates,
        "risk_tone": risk_tone,
        "analysis": (
            f"Makro: 24s {mcap_pct:+.1f}% · BTC dom %{btc_dom:.1f} · "
            f"USD/TRY {usd_try:,.2f}" if usd_try else f"Makro: 24s {mcap_pct:+.1f}% · BTC dom %{btc_dom:.1f}"
        ),
        "source": "coingecko+frankfurter",
        "real_data": True,
    }
