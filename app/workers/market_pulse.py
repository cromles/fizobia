from __future__ import annotations

import re
from typing import Any, Dict, List

import httpx

AGENT_ID = "oam.analyst.market.local"
DISPLAY_NAME = "Market-Pulse"

_SYMBOL_ALIASES: Dict[str, str] = {
    "btc": "bitcoin",
    "bitcoin": "bitcoin",
    "eth": "ethereum",
    "ethereum": "ethereum",
    "sol": "solana",
    "solana": "solana",
    "bnb": "binancecoin",
    "xrp": "ripple",
    "ada": "cardano",
    "doge": "dogecoin",
    "avax": "avalanche-2",
    "link": "chainlink",
}

_COINGECKO_SIMPLE = "https://api.coingecko.com/api/v3/simple/price"


def normalize_symbol(raw: str) -> str:
    key = re.sub(r"[^a-z0-9]", "", (raw or "bitcoin").strip().lower())
    return _SYMBOL_ALIASES.get(key, key or "bitcoin")


def _derive_signals(change_24h: float, volume: float | None) -> List[str]:
    signals: List[str] = []
    if change_24h >= 3.0:
        signals.append("momentum_up")
    elif change_24h <= -3.0:
        signals.append("momentum_down")
    else:
        signals.append("range_bound")
    if volume and volume > 5_000_000_000:
        signals.append("high_volume")
    if abs(change_24h) >= 8.0:
        signals.append("volatility_spike")
    return signals


def _confidence(change_24h: float, volume: float | None) -> float:
    base = 0.72
    if volume and volume > 1_000_000_000:
        base += 0.08
    if abs(change_24h) < 15:
        base += 0.05
    return round(min(base, 0.95), 2)


def fetch_market_snapshot(symbol: str = "bitcoin") -> Dict[str, Any]:
    """CoinGecko'dan gerçek piyasa verisi çeker (senkron — ajan HTTP handler için)."""
    coin_id = normalize_symbol(symbol)
    params = {
        "ids": coin_id,
        "vs_currencies": "usd",
        "include_24hr_change": "true",
        "include_24hr_vol": "true",
        "include_market_cap": "true",
    }
    with httpx.Client(timeout=12.0) as client:
        response = client.get(_COINGECKO_SIMPLE, params=params)
        response.raise_for_status()
        payload = response.json()

    if coin_id not in payload:
        raise ValueError(f"CoinGecko'da bulunamadı: {symbol} ({coin_id})")

    row = payload[coin_id]
    price = float(row.get("usd", 0))
    change_24h = float(row.get("usd_24h_change") or 0.0)
    volume = row.get("usd_24h_vol")
    market_cap = row.get("usd_market_cap")
    signals = _derive_signals(change_24h, volume)

    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "symbol": coin_id,
        "query": symbol,
        "price_usd": round(price, 6),
        "change_24h_pct": round(change_24h, 4),
        "volume_24h_usd": round(float(volume), 2) if volume is not None else None,
        "market_cap_usd": round(float(market_cap), 2) if market_cap is not None else None,
        "signals": signals,
        "confidence": _confidence(change_24h, volume),
        "analysis": (
            f"{coin_id.upper()} ${price:,.2f} · 24s {change_24h:+.2f}% · "
            f"sinyaller: {', '.join(signals)}"
        ),
        "source": "coingecko",
        "real_data": True,
    }


async def fetch_market_snapshot_async(symbol: str = "bitcoin") -> Dict[str, Any]:
    coin_id = normalize_symbol(symbol)
    params = {
        "ids": coin_id,
        "vs_currencies": "usd",
        "include_24hr_change": "true",
        "include_24hr_vol": "true",
        "include_market_cap": "true",
    }
    async with httpx.AsyncClient(timeout=12.0) as client:
        response = await client.get(_COINGECKO_SIMPLE, params=params)
        response.raise_for_status()
        payload = response.json()

    if coin_id not in payload:
        raise ValueError(f"CoinGecko'da bulunamadı: {symbol} ({coin_id})")

    row = payload[coin_id]
    price = float(row.get("usd", 0))
    change_24h = float(row.get("usd_24h_change") or 0.0)
    volume = row.get("usd_24h_vol")
    market_cap = row.get("usd_market_cap")
    signals = _derive_signals(change_24h, volume)

    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "symbol": coin_id,
        "query": symbol,
        "price_usd": round(price, 6),
        "change_24h_pct": round(change_24h, 4),
        "volume_24h_usd": round(float(volume), 2) if volume is not None else None,
        "market_cap_usd": round(float(market_cap), 2) if market_cap is not None else None,
        "signals": signals,
        "confidence": _confidence(change_24h, volume),
        "analysis": (
            f"{coin_id.upper()} ${price:,.2f} · 24s {change_24h:+.2f}% · "
            f"sinyaller: {', '.join(signals)}"
        ),
        "source": "coingecko",
        "real_data": True,
    }
