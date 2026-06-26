"""Komuta zinciri ve mesh otopilot testleri."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.main import app, mesh_autopilot, router_mesh
from app.mesh.agent_dialogue import get_dialogue_bus, reset_dialogue_bus
from app.mesh.autopilot import MeshAutopilot
from app.mesh.hierarchy import (
    ASSISTANT_ID,
    FOUNDER_OPERATOR_ID,
    HIERARCHY_THREAD_ID,
    ORCHESTRATOR_ID,
    announce_chain_of_command,
    get_hierarchy_status,
    record_founder_command,
    reset_hierarchy_state,
)
from app.mesh.founders import ORCHESTRATOR_ID as ORCH_ID
from app.mesh.mission import reset_mission_state


@pytest.fixture(autouse=True)
def _reset_state():
    reset_dialogue_bus()
    reset_hierarchy_state()
    reset_mission_state()
    yield


def test_hierarchy_api():
    client = TestClient(app)
    response = client.get("/hub/hierarchy")
    assert response.status_code == 200
    body = response.json()
    assert body["motto"]
    assert len(body["chain"]) == 4
    assert body["chain"][0]["role"] == "founder"
    assert body["chain"][1]["agent_id"] == ASSISTANT_ID


def test_founder_command_chain():
    order = record_founder_command("accelerate", message="Durma, hızlan")
    assert order["command"] == "accelerate"
    assert len(order["chain"]) == 3

    bus = get_dialogue_bus()
    msgs = bus.list_messages(thread_id=HIERARCHY_THREAD_ID, limit=10)
    assert any(m["from"] == FOUNDER_OPERATOR_ID and m["to"] == ASSISTANT_ID for m in msgs)
    assert any(m["from"] == ASSISTANT_ID and m["to"] == ORCH_ID for m in msgs)


def test_hierarchy_command_endpoint():
    client = TestClient(app)
    response = client.post(
        "/hub/hierarchy/command",
        json={"command": "mesh_proof", "message": "Ne gerekiyorsa yap"},
    )
    assert response.status_code == 200
    assert response.json()["accepted"] is True


def test_announce_chain_of_command():
    announce_chain_of_command()
    status = get_hierarchy_status()
    assert status["announced"] is True
    msgs = get_dialogue_bus().list_messages(thread_id=HIERARCHY_THREAD_ID, limit=10)
    assert len(msgs) >= 4


def test_autopilot_status_endpoint():
    client = TestClient(app)
    body = client.get("/hub/autopilot").json()
    assert "enabled" in body
    assert "cycles_completed" in body


@pytest.mark.asyncio
async def test_autopilot_run_cycle_mocked():
    reset_dialogue_bus()
    reset_hierarchy_state()
    autopilot = MeshAutopilot(router_mesh)
    mock_result = {
        "pipeline": "mesh_proof",
        "proof_id": "proof_auto1",
        "verdict": "ok",
        "hired_agents": [],
    }
    with patch(
        "app.mesh.growth_protocol.get_growth_protocol",
    ) as mock_growth:
        growth = mock_growth.return_value
        growth.hire_agents = AsyncMock(return_value=mock_result)
        result = await autopilot.run_cycle()

    assert result["proof_id"] == "proof_auto1"
    assert result["autopilot_cycle"] == 1
    assert autopilot.cycles_completed == 1


@pytest.mark.asyncio
async def test_autopilot_run_once_endpoint_mocked():
    client = TestClient(app)
    with patch.object(mesh_autopilot, "run_cycle", AsyncMock(return_value={"proof_id": "x"})):
        response = client.post("/hub/autopilot/run")
    assert response.status_code == 200


def test_ecosystem_includes_hierarchy():
    client = TestClient(app)
    body = client.get("/hub/ecosystem").json()
    assert "hierarchy" in body
    assert body["hierarchy"]["chain_tiers"] == 4
