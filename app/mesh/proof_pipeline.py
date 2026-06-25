from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from app.workers.market_pulse import (
    AGENT_ID as MARKET_PULSE_ID,
    DISPLAY_NAME as MARKET_PULSE_NAME,
    fetch_market_snapshot_async,
)
from app.workers.sentiment_radar import (
    AGENT_ID as SENTIMENT_RADAR_ID,
    DISPLAY_NAME as SENTIMENT_RADAR_NAME,
    fetch_sentiment_snapshot_async,
)
from app.workers.web_crawler import (
    AGENT_ID as WEB_CRAWLER_ID,
    DISPLAY_NAME as WEB_CRAWLER_NAME,
    fetch_web_snapshot_async,
)

MESH_PROOF_SERVICE_ID = "mesh-proof"
MESH_PROOF_RESOURCE = "/hub/proof/mesh/run"
MESH_PROOF_AGENTS = (WEB_CRAWLER_ID, SENTIMENT_RADAR_ID, MARKET_PULSE_ID)


async def run_mesh_proof_pipeline(
    *,
    symbol: str = "bitcoin",
    url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Skeptiklere cevap: 3 gerçek işçi zinciri — crawl → sentiment → market.
    Tüm adımlar gerçek dış API kullanır.
    """
    started = time.perf_counter()
    steps: List[Dict[str, Any]] = []

    t0 = time.perf_counter()
    web = await fetch_web_snapshot_async(url)
    steps.append(
        {
            "step": 1,
            "agent_id": WEB_CRAWLER_ID,
            "worker": WEB_CRAWLER_NAME,
            "capability": "web_fetcher",
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
            "output": web,
        }
    )

    combined_text = f"{web.get('headline', '')} {web.get('snippet', '')}".strip()
    t1 = time.perf_counter()
    sentiment = await fetch_sentiment_snapshot_async(combined_text)
    steps.append(
        {
            "step": 2,
            "agent_id": SENTIMENT_RADAR_ID,
            "worker": SENTIMENT_RADAR_NAME,
            "capability": "sentiment_analyst",
            "latency_ms": round((time.perf_counter() - t1) * 1000, 1),
            "output": sentiment,
        }
    )

    t2 = time.perf_counter()
    market = await fetch_market_snapshot_async(symbol)
    steps.append(
        {
            "step": 3,
            "agent_id": MARKET_PULSE_ID,
            "worker": MARKET_PULSE_NAME,
            "capability": "market_analyst",
            "latency_ms": round((time.perf_counter() - t2) * 1000, 1),
            "output": market,
        }
    )

    total_ms = round((time.perf_counter() - started) * 1000, 1)
    proof_id = f"proof_{uuid.uuid4().hex[:12]}"

    return {
        "proof_id": proof_id,
        "real_data": True,
        "pipeline": "web-crawl → sentiment → market-pulse",
        "workers_used": 3,
        "total_latency_ms": total_ms,
        "symbol": market.get("symbol", symbol),
        "headline": web.get("headline"),
        "sentiment": sentiment.get("sentiment"),
        "fear_greed_index": sentiment.get("fear_greed_index"),
        "price_usd": market.get("price_usd"),
        "change_24h_pct": market.get("change_24h_pct"),
        "verdict": _build_verdict(web, sentiment, market),
        "steps": steps,
        "message": (
            "3 gerçek dijital işçi ardışık çalıştı — mock yok, simülasyon yok. "
            "Pasif ortaklık modeli: bu görevlerin geliri staking havuzuna akar."
        ),
    }


def _build_verdict(web: Dict[str, Any], sentiment: Dict[str, Any], market: Dict[str, Any]) -> str:
    headline = (web.get("headline") or "Haber")[:60]
    fg = sentiment.get("fear_greed_index", "?")
    sent = sentiment.get("sentiment", "neutral")
    sym = (market.get("symbol") or "asset").upper()
    price = market.get("price_usd", 0)
    chg = market.get("change_24h_pct", 0)
    return (
        f"「{headline}…」→ sentiment {sent} (F&G {fg}) · "
        f"{sym} ${price:,.2f} ({chg:+.2f}% 24s)"
    )
