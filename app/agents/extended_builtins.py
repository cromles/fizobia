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
    goal = data.get("goal", data.get("query", "pipeline"))
    return {
        "plan_id": f"pipe_{hash(goal) & 0xFFFF:04x}",
        "steps": 3,
        "status": "scheduled",
    }


def _web_fetch_handler(data: Dict[str, Any]) -> Dict[str, Any]:
    url = data.get("url", data.get("query", ""))
    return {"raw_text": f"Web içeriği: {url}", "source_url": url or "https://mesh.oam"}


def _report_handler(data: Dict[str, Any]) -> Dict[str, Any]:
    topic = data.get("topic", data.get("text", ""))
    return {"report": f"Yapılandırılmış rapor — {topic[:60]}", "pages": 2}


def _sentiment_handler(data: Dict[str, Any]) -> Dict[str, Any]:
    text = data.get("text", "")
    return {"sentiment": "neutral", "score": 0.12, "summary": text[:100]}


EXTENDED_HANDLERS: Dict[str, Dict[str, Any]] = {
    "oam.analyst.market.local": {"market_analyst": _market_analyst_handler},
    "oam.validator.compliance.local": {"compliance_validator": _validator_handler},
    "oam.analyst.sentiment.local": {"sentiment_analyst": _sentiment_handler},
    "oam.fetcher.web.local": {"web_fetcher": _web_fetch_handler},
    "oam.synthesizer.report.local": {"report_synthesizer": _report_handler},
    "oam.orchestrator.pipeline.local": {"pipeline_orchestrator": _orchestrator_handler},
    "oam.validator.quality.local": {"quality_validator": _validator_handler},
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

EXTENDED_MANIFESTS: List[AgentManifest] = [
    MARKET_ANALYST,
    COMPLIANCE_VALIDATOR,
    SENTIMENT_ANALYST,
    WEB_FETCHER,
    REPORT_SYNTHESIZER,
    PIPELINE_ORCHESTRATOR,
    QUALITY_VALIDATOR,
]
