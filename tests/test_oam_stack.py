import pytest

from app.matching.semantic_matcher import SemanticCapabilityMatcher
from app.planning.plan_compiler import PlanCompiler
from app.protocol.schemas import AgentCapability, AgentManifest
from app.registry.agent_registry import InMemoryAgentRegistry
from app.validation.execution_validator import ExecutionValidator


def _registry_with_agents() -> InMemoryAgentRegistry:
    registry = InMemoryAgentRegistry()
    registry.register(
        AgentManifest(
            agent_id="fetcher",
            endpoint="http://fetcher",
            capabilities=[
                AgentCapability(
                    name="data_fetcher",
                    description="Veri çekme",
                    input_schema={
                        "type": "object",
                        "properties": {"query": {"type": "string"}},
                        "required": ["query"],
                    },
                    output_schema={
                        "type": "object",
                        "properties": {"raw_text": {"type": "string"}},
                        "required": ["raw_text"],
                    },
                )
            ],
        )
    )
    registry.register(
        AgentManifest(
            agent_id="synth",
            endpoint="http://synth",
            capabilities=[
                AgentCapability(
                    name="synthesizer",
                    description="Sentez ve özet",
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
    )
    return registry


def test_semantic_matcher_finds_capability():
    matcher = SemanticCapabilityMatcher()
    cap = AgentCapability(
        name="data_fetcher",
        description="Web verisi çeker",
        input_schema={},
        output_schema={},
    )
    score = matcher.score_need_to_capability("veri çek", cap)
    assert score > 0.15


@pytest.mark.asyncio
async def test_plan_compiler_builds_chain_from_goal():
    registry = _registry_with_agents()
    compiler = PlanCompiler()
    plan = await compiler.compile_plan("analiz raporu üret", {"query": "OAM"}, registry)
    assert len(plan.graph) >= 2
    assert plan.graph[1].depends_on == [plan.graph[0].task_id]


def test_execution_validator_rejects_invalid_output():
    validator = ExecutionValidator()
    valid, mismatches = validator.validate_output(
        {"summary": 123},
        {
            "type": "object",
            "properties": {"summary": {"type": "string"}},
            "required": ["summary"],
        },
    )
    assert valid is False
    assert mismatches
