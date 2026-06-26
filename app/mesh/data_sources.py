"""Ücretsiz dış veri kaynakları — katalog ve sağlık kontrolü."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

import httpx

FREE_DATA_SOURCES: List[Dict[str, Any]] = [
    {
        "id": "coingecko",
        "name": "CoinGecko",
        "endpoint": "https://api.coingecko.com/api/v3/simple/price",
        "auth": "none",
        "worker": "market_pulse",
        "agent_id": "oam.analyst.market.local",
        "use": "Kripto fiyat, hacim, market cap",
    },
    {
        "id": "alternative_me",
        "name": "Alternative.me Fear & Greed",
        "endpoint": "https://api.alternative.me/fng/",
        "auth": "none",
        "worker": "sentiment_radar",
        "agent_id": "oam.analyst.sentiment.local",
        "use": "Kripto piyasa duyarlılığı",
    },
    {
        "id": "frankfurter",
        "name": "Frankfurter (ECB)",
        "endpoint": "https://api.frankfurter.dev/v1/latest",
        "auth": "none",
        "worker": "fx_pulse",
        "agent_id": "oam.analyst.fx.local",
        "use": "USD/TRY ve döviz kurları",
    },
    {
        "id": "defillama",
        "name": "DefiLlama",
        "endpoint": "https://api.llama.fi/v2/chains",
        "auth": "none",
        "worker": "defi_pulse",
        "agent_id": "oam.analyst.defi.local",
        "use": "DeFi zincir TVL",
    },
    {
        "id": "mempool_space",
        "name": "Mempool.space",
        "endpoint": "https://mempool.space/api/v1/fees/recommended",
        "auth": "none",
        "worker": "btc_network",
        "agent_id": "oam.watcher.btcnet.local",
        "use": "BTC blok yüksekliği ve ücretler",
    },
    {
        "id": "blockchain_info",
        "name": "Blockchain.info",
        "endpoint": "https://blockchain.info/ticker",
        "auth": "none",
        "worker": "btc_network",
        "agent_id": "oam.watcher.btcnet.local",
        "use": "BTC spot fiyat (yedek kaynak)",
    },
    {
        "id": "coindesk_rss",
        "name": "CoinDesk RSS",
        "endpoint": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "auth": "none",
        "worker": "web_crawler",
        "agent_id": "oam.fetcher.web.local",
        "use": "Haber tarama / makale araştırma",
    },
    {
        "id": "gemini_llm",
        "name": "Google Gemini",
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/openai",
        "auth": "api_key",
        "worker": "llm_client",
        "agent_id": None,
        "use": "Şiir, metin, arena üretimi (anahtarlı)",
    },
]


async def _probe_url(url: str) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            response = await client.get(url)
            return {
                "reachable": response.status_code < 500,
                "status_code": response.status_code,
            }
    except Exception as exc:
        return {"reachable": False, "error": str(exc)[:120]}


async def probe_data_sources() -> List[Dict[str, Any]]:
    """Tüm kaynaklar için hızlı erişim kontrolü."""
    tasks = [_probe_url(src["endpoint"]) for src in FREE_DATA_SOURCES]
    results = await asyncio.gather(*tasks)
    out: List[Dict[str, Any]] = []
    for src, probe in zip(FREE_DATA_SOURCES, results):
        out.append({**src, "probe": probe})
    return out


def list_data_sources() -> Dict[str, Any]:
    """Anahtarsız katalog — probe olmadan."""
    no_key = [s for s in FREE_DATA_SOURCES if s["auth"] == "none"]
    keyed = [s for s in FREE_DATA_SOURCES if s["auth"] != "none"]
    return {
        "total": len(FREE_DATA_SOURCES),
        "free_no_auth": len(no_key),
        "keyed": len(keyed),
        "sources": FREE_DATA_SOURCES,
    }
