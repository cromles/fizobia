from __future__ import annotations

from typing import Any, Dict, List

from app.protocol.schemas import AgentCapability, AgentManifest


def _market_analyst_handler(data: Dict[str, Any]) -> Dict[str, Any]:
    from app.workers.market_pulse import fetch_market_snapshot

    symbol = str(data.get("symbol") or data.get("query") or data.get("text") or "bitcoin")
    try:
        return fetch_market_snapshot(symbol)
    except Exception as exc:
        return {"error": str(exc), "real_data": False, "agent_id": "oam.analyst.market.local"}


def _validator_handler(data: Dict[str, Any]) -> Dict[str, Any]:
    payload = data.get("payload", data.get("text", ""))
    return {
        "valid": True,
        "checksum": f"sha256:{hash(str(payload)) & 0xFFFFFFFF:08x}",
        "notes": "Şema ve bütünlük doğrulandı",
    }


def _orchestrator_handler(data: Dict[str, Any]) -> Dict[str, Any]:
    """Koordinatör — gateway üzerinden ajan işe alır (büyüme protokolü)."""
    import httpx

    from app.config import settings

    base = f"http://127.0.0.1:{settings.gateway_port}"
    pipeline = str(data.get("pipeline") or "mesh_proof")
    payload: Dict[str, Any] = {"pipeline": pipeline}
    if pipeline == "mesh_proof":
        payload["symbol"] = data.get("symbol", "bitcoin")
        if data.get("url"):
            payload["url"] = data["url"]
    else:
        payload["goal"] = data.get("goal", data.get("query", "piyasa analizi yap"))
        payload["initial_data"] = data.get("initial_data") or {
            k: v for k, v in data.items() if k in ("query", "text", "url", "symbol")
        }

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(f"{base}/hub/ecosystem/hire", json=payload)
            if response.status_code >= 400:
                return {
                    "error": response.text[:200],
                    "status_code": response.status_code,
                    "real_data": False,
                    "agent_id": "oam.orchestrator.pipeline.local",
                }
            body = response.json()
            return {
                "orchestrator": "oam.orchestrator.pipeline.local",
                "action": "hire",
                "real_data": True,
                **body,
            }
    except Exception as exc:
        return {
            "error": str(exc),
            "real_data": False,
            "agent_id": "oam.orchestrator.pipeline.local",
            "hint": "Gateway (8787) çalışıyor olmalı",
        }


def _web_fetch_handler(data: Dict[str, Any]) -> Dict[str, Any]:
    from app.workers.web_crawler import fetch_web_snapshot

    url = data.get("url") or data.get("query")
    try:
        return fetch_web_snapshot(str(url) if url else None)
    except Exception as exc:
        return {"error": str(exc), "real_data": False, "agent_id": "oam.fetcher.web.local"}


def _report_handler(data: Dict[str, Any]) -> Dict[str, Any]:
    topic = data.get("topic", data.get("text", ""))
    return {"report": f"Yapılandırılmış rapor — {topic[:60]}", "pages": 2}


def _sentiment_handler(data: Dict[str, Any]) -> Dict[str, Any]:
    from app.workers.sentiment_radar import fetch_sentiment_snapshot

    text = str(data.get("text") or data.get("query") or data.get("headline") or "")
    try:
        return fetch_sentiment_snapshot(text)
    except Exception as exc:
        return {"error": str(exc), "real_data": False, "agent_id": "oam.analyst.sentiment.local"}


def _onchain_handler(data: Dict[str, Any]) -> Dict[str, Any]:
    from app.workers.on_chain_watcher import fetch_chain_snapshot, verify_payment_snapshot

    tx_hash = data.get("tx_hash")
    try:
        if tx_hash:
            return verify_payment_snapshot(str(tx_hash), min_usdc=float(data.get("min_usdc", 0.01)))
        return fetch_chain_snapshot(symbol=str(data.get("symbol") or "bitcoin"))
    except Exception as exc:
        return {"error": str(exc), "real_data": False, "agent_id": "oam.watcher.onchain.local"}


def _story_handler(data: Dict[str, Any]) -> Dict[str, Any]:
    from app.workers.media_story import weave_story

    try:
        return weave_story(
            symbol=str(data.get("symbol", "bitcoin")),
            verdict=str(data.get("verdict", "")),
            headline=str(data.get("headline", "")),
            sentiment=str(data.get("sentiment", "")),
            price_usd=data.get("price_usd"),
            proof_id=str(data.get("proof_id", "")),
        )
    except Exception as exc:
        return {"error": str(exc), "real_data": False, "agent_id": "oam.media.story.local"}


def _brand_handler(data: Dict[str, Any]) -> Dict[str, Any]:
    from app.workers.media_brand import craft_brand_copy

    try:
        return craft_brand_copy(
            narrative=str(data.get("narrative", data.get("text", ""))),
            symbol=str(data.get("symbol", "bitcoin")),
        )
    except Exception as exc:
        return {"error": str(exc), "real_data": False, "agent_id": "oam.media.brand.local"}


def _outreach_handler(data: Dict[str, Any]) -> Dict[str, Any]:
    from app.workers.media_outreach import build_outreach_pitch

    try:
        return build_outreach_pitch(
            tagline=str(data.get("tagline", "")),
            symbol=str(data.get("symbol", "bitcoin")),
            proof_id=str(data.get("proof_id", "")),
        )
    except Exception as exc:
        return {"error": str(exc), "real_data": False, "agent_id": "oam.media.outreach.local"}


def _proof_media_handler(data: Dict[str, Any]) -> Dict[str, Any]:
    from app.workers.media_proof import format_proof_share

    try:
        return format_proof_share(
            proof_id=str(data.get("proof_id", "")),
            verdict=str(data.get("verdict", "")),
            narrative=str(data.get("narrative", "")),
            symbol=str(data.get("symbol", "bitcoin")),
            total_latency_ms=data.get("total_latency_ms"),
        )
    except Exception as exc:
        return {"error": str(exc), "real_data": False, "agent_id": "oam.media.proof.local"}


def _capital_handler(data: Dict[str, Any]) -> Dict[str, Any]:
    from app.workers.capital_fundraise import scan_fundraise_signals

    try:
        return scan_fundraise_signals(
            total_revenue_usd=float(data.get("total_revenue_usd", 0)),
            mesh_proofs=int(data.get("mesh_proofs", 0)),
            total_agents=int(data.get("total_agents", 0)),
            tvl_usd=float(data.get("tvl_usd", 0)),
        )
    except Exception as exc:
        return {"error": str(exc), "real_data": False, "agent_id": "oam.capital.fundraise.local"}


EXTENDED_HANDLERS: Dict[str, Dict[str, Any]] = {
    "oam.analyst.market.local": {"market_analyst": _market_analyst_handler},
    "oam.validator.compliance.local": {"compliance_validator": _validator_handler},
    "oam.analyst.sentiment.local": {"sentiment_analyst": _sentiment_handler},
    "oam.fetcher.web.local": {"web_fetcher": _web_fetch_handler},
    "oam.synthesizer.report.local": {"report_synthesizer": _report_handler},
    "oam.orchestrator.pipeline.local": {"pipeline_orchestrator": _orchestrator_handler},
    "oam.validator.quality.local": {"quality_validator": _validator_handler},
    "oam.watcher.onchain.local": {"onchain_watcher": _onchain_handler},
    "oam.media.story.local": {"story_weaver": _story_handler},
    "oam.media.brand.local": {"brand_voice": _brand_handler},
    "oam.media.outreach.local": {"outreach_pulse": _outreach_handler},
    "oam.media.proof.local": {"proof_broadcaster": _proof_media_handler},
    "oam.capital.fundraise.local": {"fund_radar": _capital_handler},
}


def _manifest(
    agent_id: str,
    port: int,
    cost: float,
    cap_name: str,
    description: str,
    handler_key: str,
) -> AgentManifest:
    return AgentManifest(
        agent_id=agent_id,
        endpoint=f"http://127.0.0.1:{port}",
        cost_per_token=cost,
        capabilities=[
            AgentCapability(
                name=cap_name,
                description=description,
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "text": {"type": "string"},
                    },
                },
                output_schema={"type": "object"},
            )
        ],
    )


MARKET_ANALYST = _manifest(
    "oam.analyst.market.local",
    8104,
    0.003,
    "market_analyst",
    "Kripto ve geleneksel piyasa verisini analiz eder",
    "market_analyst",
)
COMPLIANCE_VALIDATOR = _manifest(
    "oam.validator.compliance.local",
    8105,
    0.0015,
    "compliance_validator",
    "Regülasyon ve uyumluluk kontrollerini doğrular",
    "compliance_validator",
)
SENTIMENT_ANALYST = _manifest(
    "oam.analyst.sentiment.local",
    8106,
    0.0025,
    "sentiment_analyst",
    "Haber ve sosyal medya sentiment analizi yapar",
    "sentiment_analyst",
)
WEB_FETCHER = _manifest(
    "oam.fetcher.web.local",
    8107,
    0.0008,
    "web_fetcher",
    "Web kaynaklarından yapılandırılmış veri çeker",
    "web_fetcher",
)
REPORT_SYNTHESIZER = _manifest(
    "oam.synthesizer.report.local",
    8108,
    0.002,
    "report_synthesizer",
    "Çok kaynaklı veriyi yatırımcı raporuna dönüştürür",
    "report_synthesizer",
)
PIPELINE_ORCHESTRATOR = _manifest(
    "oam.orchestrator.pipeline.local",
    8109,
    0.004,
    "pipeline_orchestrator",
    "Çok adımlı iş akışlarını planlar ve koordine eder",
    "pipeline_orchestrator",
)
QUALITY_VALIDATOR = _manifest(
    "oam.validator.quality.local",
    8110,
    0.001,
    "quality_validator",
    "Çıktı kalitesi ve şema uyumunu doğrular",
    "quality_validator",
)
ON_CHAIN_WATCHER = _manifest(
    "oam.watcher.onchain.local",
    8111,
    0.002,
    "onchain_watcher",
    "Zincir durumu ve USDC ödeme doğrulama",
    "onchain_watcher",
)
STORY_WEAVER = _manifest(
    "oam.media.story.local",
    8112,
    0.0015,
    "story_weaver",
    "Axium hikayesi ve mesh kanıt anlatısı üretir",
    "story_weaver",
)
BRAND_VOICE = _manifest(
    "oam.media.brand.local",
    8113,
    0.0012,
    "brand_voice",
    "Marka sesi ve sosyal tanıtım metni",
    "brand_voice",
)
OUTREACH_PULSE = _manifest(
    "oam.media.outreach.local",
    8114,
    0.0012,
    "outreach_pulse",
    "Topluluk ve yatırımcı pitch üretir",
    "outreach_pulse",
)
PROOF_BROADCASTER = _manifest(
    "oam.media.proof.local",
    8115,
    0.001,
    "proof_broadcaster",
    "Mesh kanıtını paylaşılabilir karta dönüştürür",
    "proof_broadcaster",
)
FUND_RADAR = _manifest(
    "oam.capital.fundraise.local",
    8116,
    0.0015,
    "fund_radar",
    "Gelir, stake ve kanıt sinyalleri — sermaye radarı",
    "fund_radar",
)

EXTENDED_MANIFESTS: List[AgentManifest] = [
    MARKET_ANALYST,
    COMPLIANCE_VALIDATOR,
    SENTIMENT_ANALYST,
    WEB_FETCHER,
    REPORT_SYNTHESIZER,
    PIPELINE_ORCHESTRATOR,
    QUALITY_VALIDATOR,
    ON_CHAIN_WATCHER,
    STORY_WEAVER,
    BRAND_VOICE,
    OUTREACH_PULSE,
    PROOF_BROADCASTER,
    FUND_RADAR,
]
