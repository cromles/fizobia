from __future__ import annotations

import asyncio
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
_BLOCKCHAIN_TICKER = "https://blockchain.info/ticker"


def _fetch_blockchain_info_btc() -> Dict[str, Any]:
    """CoinGecko yedek — blockchain.info spot BTC."""
    with httpx.Client(timeout=12.0) as client:
        response = client.get(_BLOCKCHAIN_TICKER)
        response.raise_for_status()
        payload = response.json()
    usd = payload.get("USD", {})
    price = float(usd.get("last") or usd.get("15m") or 0)
    return {
        "price_usd": round(price, 6),
        "change_24h_pct": None,
        "volume_24h_usd": None,
        "market_cap_usd": None,
        "source": "blockchain.info",
    }


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
    """CoinGecko'dan gerçek piyasa verisi; BTC için blockchain.info yedek."""
    coin_id = normalize_symbol(symbol)
    source = "coingecko"
    try:
        params = {
            "ids": coin_id,
            "vs_currencies": "usd,try",
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
        price_try = row.get("try")
    except Exception:
        if coin_id != "bitcoin":
            raise
        fallback = _fetch_blockchain_info_btc()
        price = fallback["price_usd"]
        change_24h = 0.0
        volume = None
        market_cap = None
        price_try = None
        source = fallback["source"]

    signals = _derive_signals(change_24h or 0.0, volume)

    result: Dict[str, Any] = {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "symbol": coin_id,
        "query": symbol,
        "price_usd": round(price, 6),
        "change_24h_pct": round(change_24h, 4) if change_24h is not None else None,
        "volume_24h_usd": round(float(volume), 2) if volume is not None else None,
        "market_cap_usd": round(float(market_cap), 2) if market_cap is not None else None,
        "signals": signals,
        "confidence": _confidence(change_24h or 0.0, volume),
        "analysis": (
            f"{coin_id.upper()} ${price:,.2f} · 24s {change_24h:+.2f}% · "
            f"sinyaller: {', '.join(signals)}"
            if change_24h is not None
            else f"{coin_id.upper()} ${price:,.2f} · yedek kaynak · sinyaller: {', '.join(signals)}"
        ),
        "source": source,
        "real_data": True,
    }
    if price_try is not None:
        result["price_try"] = round(float(price_try), 2)
    return result


async def fetch_market_snapshot_async(symbol: str = "bitcoin") -> Dict[str, Any]:
    return await asyncio.to_thread(fetch_market_snapshot, symbol)
