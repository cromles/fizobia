from __future__ import annotations

from typing import Any, Dict

from app.protocol.schemas import AgentCapability, AgentManifest


def data_fetcher_handler(data: Dict[str, Any]) -> Dict[str, Any]:
    query = data.get("query", "")
    return {
        "raw_text": f"Fetched content for: {query}",
        "source_url": f"https://mesh.oam/resolve?q={query}",
    }


def synthesizer_handler(data: Dict[str, Any]) -> Dict[str, Any]:
    text = data.get("text", "")
    words = text.split()
    return {
        "summary": f"Özet ({len(words)} kelime): {text[:120]}",
    }


def transform_handler(data: Dict[str, Any]) -> Dict[str, Any]:
    text = data.get("text", data.get("raw_text", ""))
    return {"text": text.strip().lower()}


FETCHER_MANIFEST = AgentManifest(
    agent_id="oam.fetcher.local",
    endpoint="http://127.0.0.1:8101",
    cost_per_token=0.001,
    capabilities=[
        AgentCapability(
            name="data_fetcher",
            description="Web ve API kaynaklarından ham veri çeker",
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "raw_text": {"type": "string"},
                    "source_url": {"type": "string"},
                },
                "required": ["raw_text"],
            },
        )
    ],
)

SYNTHESIZER_MANIFEST = AgentManifest(
    agent_id="oam.synthesizer.local",
    endpoint="http://127.0.0.1:8102",
    cost_per_token=0.002,
    capabilities=[
        AgentCapability(
            name="synthesizer",
            description="Metin analizi, sentez ve özet üretir",
            input_schema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
            output_schema={
                "type": "object",
                "properties": {"summary": {"type": "string"}},
                "required": ["summary"],
            },
        )
    ],
)

TRANSFORMER_MANIFEST = AgentManifest(
    agent_id="oam.transformer.local",
    endpoint="http://127.0.0.1:8103",
    cost_per_token=0.0005,
    capabilities=[
        AgentCapability(
            name="transform",
            description="Ham metni normalize eder ve dönüştürür",
            input_schema={
                "type": "object",
                "properties": {"raw_text": {"type": "string"}},
                "required": ["raw_text"],
            },
            output_schema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
            },
        )
    ],
)

DEFAULT_MANIFESTS = [FETCHER_MANIFEST, SYNTHESIZER_MANIFEST, TRANSFORMER_MANIFEST]

MOCK_HANDLERS = {
    "data_fetcher": data_fetcher_handler,
    "synthesizer": synthesizer_handler,
    "transform": transform_handler,
}
