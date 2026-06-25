import httpx
import pytest

from app.matching.embedding_matcher import EmbeddingCapabilityMatcher, HybridCapabilityMatcher
from app.planning.decomposer import HybridGoalDecomposer, LLMGoalDecomposer
from app.protocol.schemas import AgentCapability, AgentManifest
from app.registry.agent_registry import RegisteredCapability


def _capabilities() -> list[RegisteredCapability]:
    fetch = AgentCapability(
        name="data_fetcher",
        description="Veri çeker",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        output_schema={"type": "object", "properties": {"raw_text": {"type": "string"}}, "required": ["raw_text"]},
    )
    synth = AgentCapability(
        name="synthesizer",
        description="Özet üretir",
        input_schema={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
        output_schema={"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"]},
    )
    return [
        RegisteredCapability("a1", "http://a1", 1.0, 0.0, fetch),
        RegisteredCapability("a2", "http://a2", 1.0, 0.0, synth),
    ]


@pytest.mark.asyncio
async def test_llm_decomposer_parses_steps(monkeypatch):
    decomposer = LLMGoalDecomposer(api_key="test-key")

    async def mock_post(self, url, headers=None, json=None):
        class Response:
            status_code = 200

            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "choices": [
                        {
                            "message": {
                                "content": '{"steps": ["data_fetcher", "synthesizer"]}',
                            }
                        }
                    ]
                }

        return Response()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    steps = await decomposer.extract_capability_needs(
        "web verisini özetle",
        _capabilities(),
    )
    assert steps == ["data_fetcher", "synthesizer"]


@pytest.mark.asyncio
async def test_hybrid_decomposer_falls_back_without_api_key():
    hybrid = HybridGoalDecomposer(llm=LLMGoalDecomposer(api_key=""))
    steps = await hybrid.extract_capability_needs(
        "analiz raporu",
        _capabilities(),
    )
    assert "data_fetcher" in steps
    assert "synthesizer" in steps


@pytest.mark.asyncio
async def test_embedding_matcher_uses_api_vectors(monkeypatch):
    matcher = EmbeddingCapabilityMatcher(api_key="test-key")
    calls: list[str] = []

    async def mock_post(self, url, headers=None, json=None):
        calls.append(json["input"])

        class Response:
            status_code = 200

            def raise_for_status(self):
                return None

            def json(self):
                text = json["input"]
                if "fetcher" in text:
                    return {"data": [{"embedding": [1.0, 0.0]}]}
                if "özet" in text or "summary" in text:
                    return {"data": [{"embedding": [0.2, 0.98]}]}
                return {"data": [{"embedding": [0.9, 0.1]}]}

        return Response()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    caps = _capabilities()
    match = await matcher.find_best_capability_async("özet oluştur", caps)
    assert match is not None
    assert match[0].capability.name == "synthesizer"
    assert calls


@pytest.mark.asyncio
async def test_hybrid_matcher_falls_back_without_api_key():
    matcher = HybridCapabilityMatcher(
        embedding=EmbeddingCapabilityMatcher(api_key=""),
    )
    caps = _capabilities()
    match = await matcher.find_best_capability_async("data_fetcher", caps)
    assert match is not None
    assert match[0].capability.name == "data_fetcher"
