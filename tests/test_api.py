import pytest
from fastapi.testclient import TestClient

from app.api.main import app, router_mesh
from app.agents.builtins import FETCHER_MANIFEST, SYNTHESIZER_MANIFEST
from app.registry.agent_registry import InMemoryAgentRegistry


@pytest.fixture(autouse=True)
def clean_registry():
    router_mesh.registry = InMemoryAgentRegistry()
    yield


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["protocol"] == "OAM"
    assert response.json()["registry"] == "memory"
    assert "planner" in response.json()
    assert "matcher" in response.json()
    assert "discovery" in response.json()


def test_register_and_compile_plan():
    client = TestClient(app)
    client.post("/agents/register", json={"manifest": FETCHER_MANIFEST.model_dump()})
    client.post("/agents/register", json={"manifest": SYNTHESIZER_MANIFEST.model_dump()})

    response = client.post(
        "/plans/compile",
        json={"user_goal": "veri analizi yap", "initial_data": {"query": "mesh"}},
    )
    assert response.status_code == 200
    plan = response.json()
    assert len(plan["graph"]) >= 2
