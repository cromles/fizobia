from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from app.mesh.agent_dialogue import get_dialogue_bus
from app.workers.market_pulse import (
    AGENT_ID as MARKET_PULSE_ID,
    DISPLAY_NAME as MARKET_PULSE_NAME,
    fetch_market_snapshot_async,
)
from app.workers.on_chain_watcher import (
    AGENT_ID as ON_CHAIN_ID,
    DISPLAY_NAME as ON_CHAIN_NAME,
    fetch_chain_snapshot_async,
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
from app.mesh.founders import ORCHESTRATOR_ID
from app.mesh.mission import pipeline_mission_opener

MESH_PROOF_SERVICE_ID = "mesh-proof"
MESH_PROOF_RESOURCE = "/hub/proof/mesh/run"
MESH_PROOF_AGENTS = (WEB_CRAWLER_ID, SENTIMENT_RADAR_ID, MARKET_PULSE_ID, ON_CHAIN_ID)


async def run_mesh_proof_pipeline(
    *,
    symbol: str = "bitcoin",
    url: Optional[str] = None,
    tx_hash: Optional[str] = None,
) -> Dict[str, Any]:
    """
    4 gerçek işçi zinciri — ajanlar birbirleriyle konuşarak çalışır.
    crawl → sentiment → market → on-chain
    """
    dialogue = get_dialogue_bus()
    thread_id = f"proof_{uuid.uuid4().hex[:8]}"
    started = time.perf_counter()
    steps: List[Dict[str, Any]] = []

    pipeline_mission_opener(thread_id)

    dialogue.say(
        ORCHESTRATOR_ID,
        WEB_CRAWLER_ID,
        f"Web taraması başlat — sembol: {symbol}",
        intent="hire_request",
        thread_id=thread_id,
    )

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
    dialogue.say(
        WEB_CRAWLER_ID,
        ORCHESTRATOR_ID,
        f"Kaynak tarandı: {web.get('headline', '')[:80]}",
        intent="task_done",
        payload={"source": web.get("source_url")},
        thread_id=thread_id,
    )

    combined_text = f"{web.get('headline', '')} {web.get('snippet', '')}".strip()
    dialogue.say(
        ORCHESTRATOR_ID,
        SENTIMENT_RADAR_ID,
        "Sentiment analizi iste — crawl çıktısını kullan",
        intent="hire_request",
        payload={"text_preview": combined_text[:120]},
        thread_id=thread_id,
    )

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
    dialogue.say(
        SENTIMENT_RADAR_ID,
        MARKET_PULSE_ID,
        f"Sentiment: {sentiment.get('sentiment')} (F&G {sentiment.get('fear_greed_index')}) — piyasa verisi lazım",
        intent="handoff",
        thread_id=thread_id,
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
    dialogue.say(
        MARKET_PULSE_ID,
        ON_CHAIN_ID,
        f"{market.get('symbol', symbol).upper()} ${market.get('price_usd', 0):,.2f} — zincir durumunu doğrula",
        intent="handoff",
        thread_id=thread_id,
    )

    dialogue.say(
        ORCHESTRATOR_ID,
        ON_CHAIN_ID,
        "On-chain snapshot al — ödeme altyapısı hazır mı?",
        intent="hire_request",
        thread_id=thread_id,
    )

    t3 = time.perf_counter()
    if tx_hash:
        from app.workers.on_chain_watcher import verify_payment_snapshot_async

        chain = await verify_payment_snapshot_async(tx_hash)
    else:
        chain = await fetch_chain_snapshot_async(symbol=symbol)
    steps.append(
        {
            "step": 4,
            "agent_id": ON_CHAIN_ID,
            "worker": ON_CHAIN_NAME,
            "capability": "onchain_watcher",
            "latency_ms": round((time.perf_counter() - t3) * 1000, 1),
            "output": chain,
        }
    )
    dialogue.say(
        ON_CHAIN_ID,
        ORCHESTRATOR_ID,
        chain.get("analysis", "Zincir doğrulandı"),
        intent="task_done",
        payload={"block": chain.get("block_number"), "network": chain.get("network")},
        thread_id=thread_id,
    )
    dialogue.say(
        ORCHESTRATOR_ID,
        "*",
        "Pipeline tamam — 4 ajan görevini bitirdi",
        intent="pipeline_complete",
        payload={"proof_thread": thread_id},
        thread_id=thread_id,
    )

    total_ms = round((time.perf_counter() - started) * 1000, 1)
    proof_id = f"proof_{uuid.uuid4().hex[:12]}"

    return {
        "proof_id": proof_id,
        "real_data": True,
        "pipeline": "web-crawl → sentiment → market → on-chain",
        "workers_used": 4,
        "dialogue_thread": thread_id,
        "dialogue_messages": len(dialogue.list_messages(thread_id=thread_id, limit=100)),
        "total_latency_ms": total_ms,
        "symbol": market.get("symbol", symbol),
        "headline": web.get("headline"),
        "sentiment": sentiment.get("sentiment"),
        "fear_greed_index": sentiment.get("fear_greed_index"),
        "price_usd": market.get("price_usd"),
        "change_24h_pct": market.get("change_24h_pct"),
        "chain_network": chain.get("network"),
        "block_number": chain.get("block_number"),
        "verdict": _build_verdict(web, sentiment, market, chain),
        "steps": steps,
        "message": (
            "4 gerçek dijital işçi konuşarak ardışık çalıştı — mock yok. "
            "Ajanlar birbirini işe aldı, zincir doğrulandı."
        ),
    }


def _build_verdict(
    web: Dict[str, Any],
    sentiment: Dict[str, Any],
    market: Dict[str, Any],
    chain: Dict[str, Any],
) -> str:
    headline = (web.get("headline") or "Haber")[:60]
    fg = sentiment.get("fear_greed_index", "?")
    sent = sentiment.get("sentiment", "neutral")
    sym = (market.get("symbol") or "asset").upper()
    price = market.get("price_usd", 0)
    chg = market.get("change_24h_pct", 0)
    net = chain.get("network", "chain")
    block = chain.get("block_number", "?")
    return (
        f"「{headline}…」→ {sent} (F&G {fg}) · "
        f"{sym} ${price:,.2f} ({chg:+.2f}% 24s) · "
        f"{net} blok #{block}"
    )
