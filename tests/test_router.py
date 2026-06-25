import pytest
import httpx

from app.core.router import OpenAgentMeshRouter
from app.protocol.schemas import AgentCapability, AgentManifest


def _fetcher_manifest() -> AgentManifest:
    return AgentManifest(
        agent_id="fetcher-1",
        endpoint="http://fetcher.local",
        capabilities=[
            AgentCapability(
                name="data_fetcher",
                description="Veri çekme ajanı",
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


def _synth_manifest() -> AgentManifest:
    return AgentManifest(
        agent_id="synth-1",
        endpoint="http://synth.local",
        capabilities=[
            AgentCapability(
                name="synthesizer",
                description="Sentez ajanı",
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


@pytest.mark.asyncio
async def test_compile_plan_builds_dependency_chain():
    router = OpenAgentMeshRouter()
    router.register_agent(_fetcher_manifest())
    router.register_agent(_synth_manifest())

    plan = await router.compile_plan("analiz raporu", {"query": "OAM"})
    assert len(plan.graph) == 2
    assert plan.graph[1].depends_on == [plan.graph[0].task_id]


@pytest.mark.asyncio
async def test_execute_plan_runs_dag_with_adapter(monkeypatch):
    router = OpenAgentMeshRouter()
    router.register_agent(_fetcher_manifest())
    router.register_agent(_synth_manifest())
    plan = await router.compile_plan("analiz", {"query": "test"})

    call_log: list[dict] = []

    async def mock_post(self, url, json=None, timeout=None):
        call_log.append({"url": url, "json": json})

        class Response:
            status_code = 200

            @staticmethod
            def json():
                if "fetcher" in url:
                    return {"raw_text": "kaynak veri"}
                return {"summary": "sentezlendi"}

        return Response()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    results = await router.execute_plan(plan)
    assert len(results) == 2
    assert call_log[1]["json"]["data"]["text"] == "kaynak veri"


@pytest.mark.asyncio
async def test_reliability_penalty_on_failure(monkeypatch):
    router = OpenAgentMeshRouter()
    manifest = _fetcher_manifest()
    router.register_agent(manifest)
    router.register_agent(_synth_manifest())

    plan = await router.compile_plan("analiz", {"query": "x"})
    plan.graph = [plan.graph[0]]

    async def mock_post(self, url, json=None, timeout=None):
        class Response:
            status_code = 500

            @staticmethod
            def json():
                return {}

        return Response()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    await router.execute_plan(plan)
    assert manifest.reliability_score < 1.0
