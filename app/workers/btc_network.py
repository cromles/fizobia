"""Bitcoin ağı — mempool.space + blockchain.info (anahtarsız)."""

from __future__ import annotations

from typing import Any, Dict

import httpx

AGENT_ID = "oam.watcher.btcnet.local"
DISPLAY_NAME = "BTC-Network"

_MEMPOOL_FEES = "https://mempool.space/api/v1/fees/recommended"
_MEMPOOL_HEIGHT = "https://mempool.space/api/blocks/tip/height"
_BLOCKCHAIN_TICKER = "https://blockchain.info/ticker"


def _fetch_mempool(client: httpx.Client) -> Dict[str, Any]:
    fees_resp = client.get(_MEMPOOL_FEES)
    fees_resp.raise_for_status()
    fees = fees_resp.json()
    height_resp = client.get(_MEMPOOL_HEIGHT)
    height_resp.raise_for_status()
    height = int(height_resp.text.strip())
    return {
        "block_height": height,
        "fees_sat_vb": {
            "fastest": fees.get("fastestFee"),
            "half_hour": fees.get("halfHourFee"),
            "hour": fees.get("hourFee"),
            "economy": fees.get("economyFee"),
            "minimum": fees.get("minimumFee"),
        },
    }


def _fetch_btc_usd(client: httpx.Client) -> float:
    response = client.get(_BLOCKCHAIN_TICKER)
    response.raise_for_status()
    payload = response.json()
    usd = payload.get("USD", {})
    return float(usd.get("last") or usd.get("15m") or 0)


def fetch_btc_network_snapshot() -> Dict[str, Any]:
    """BTC blok yüksekliği, ücretler ve spot USD fiyatı."""
    with httpx.Client(timeout=12.0) as client:
        mempool = _fetch_mempool(client)
        btc_usd = _fetch_btc_usd(client)

    fastest = mempool["fees_sat_vb"].get("fastest")
    height = mempool["block_height"]
    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "btc_usd": round(btc_usd, 2),
        "block_height": height,
        "fees_sat_vb": mempool["fees_sat_vb"],
        "mempool_congestion": (
            "yüksek" if fastest and fastest >= 30 else "normal" if fastest and fastest >= 10 else "düşük"
        ),
        "analysis": (
            f"BTC ${btc_usd:,.0f} · blok #{height:,} · "
            f"hızlı ücret {fastest} sat/vB"
        ),
        "source": "mempool.space+blockchain.info",
        "real_data": True,
    }


async def fetch_btc_network_snapshot_async() -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=12.0) as client:
        fees_resp = await client.get(_MEMPOOL_FEES)
        fees_resp.raise_for_status()
        fees = fees_resp.json()
        height_resp = await client.get(_MEMPOOL_HEIGHT)
        height_resp.raise_for_status()
        height = int(height_resp.text.strip())
        ticker_resp = await client.get(_BLOCKCHAIN_TICKER)
        ticker_resp.raise_for_status()
        ticker = ticker_resp.json()

    btc_usd = float((ticker.get("USD") or {}).get("last") or 0)
    fastest = fees.get("fastestFee")
    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "btc_usd": round(btc_usd, 2),
        "block_height": height,
        "fees_sat_vb": {
            "fastest": fees.get("fastestFee"),
            "half_hour": fees.get("halfHourFee"),
            "hour": fees.get("hourFee"),
            "economy": fees.get("economyFee"),
            "minimum": fees.get("minimumFee"),
        },
        "mempool_congestion": (
            "yüksek" if fastest and fastest >= 30 else "normal" if fastest and fastest >= 10 else "düşük"
        ),
        "analysis": (
            f"BTC ${btc_usd:,.0f} · blok #{height:,} · "
            f"hızlı ücret {fastest} sat/vB"
        ),
        "source": "mempool.space+blockchain.info",
        "real_data": True,
    }
