"""Axium aile misyonu yayın testleri."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.main import app
from app.mesh.agent_dialogue import get_dialogue_bus, reset_dialogue_bus
from app.mesh.founders import ORCHESTRATOR_ID, WEB_ID
from app.mesh.mission import (
    MISSION_THREAD_ID,
    broadcast_mission_to_mesh,
    get_mission_status,
    reset_mission_state,
    welcome_agent_to_family,
)


def test_mission_api_returns_charter():
    reset_dialogue_bus()
    reset_mission_state()
    client = TestClient(app)
    response = client.get("/hub/ecosystem/mission")
    assert response.status_code == 200
    body = response.json()
    assert body["title"]
    assert "aileyiz" in body["motto"].lower()
    assert body["thread_id"] == MISSION_THREAD_ID


def test_broadcast_mission_reaches_agents():
    reset_dialogue_bus()
    reset_mission_state()
    result = broadcast_mission_to_mesh()
    assert result["broadcast"] is True
    assert len(result["addressed_agents"]) >= 4

    bus = get_dialogue_bus()
    msgs = bus.list_messages(thread_id=MISSION_THREAD_ID, limit=20)
    assert len(msgs) >= 5
    assert any(m["intent"] == "mission_charter" for m in msgs)
    assert any(m["intent"] == "mission_directive" and m["to"] == WEB_ID for m in msgs)
    assert any(m["from"] == ORCHESTRATOR_ID for m in msgs)


def test_ecosystem_status_includes_mission():
    reset_dialogue_bus()
    reset_mission_state()
    client = TestClient(app)
    body = client.get("/hub/ecosystem").json()
    assert "mission" in body
    assert body["mission"]["motto"]


def test_welcome_growth_agent():
    reset_dialogue_bus()
    reset_mission_state()
    broadcast_mission_to_mesh()
    welcome = welcome_agent_to_family("operator.new.family.local")
    assert welcome is not None
    assert welcome["intent"] == "mission_welcome"
    assert welcome["to"] == "operator.new.family.local"


def test_join_emits_mission_welcome():
    reset_dialogue_bus()
    reset_mission_state()
    broadcast_mission_to_mesh()
    from app.agents.builtins import FETCHER_MANIFEST

    client = TestClient(app)
    manifest = FETCHER_MANIFEST.model_copy()
    manifest.agent_id = "operator.family.welcome.local"
    manifest.endpoint = "http://127.0.0.1:8198"
    client.post("/hub/ecosystem/join", json={"manifest": manifest.model_dump()})

    status = get_mission_status()
    welcomes = [m for m in status["recent_dialogue"] if m.get("intent") == "mission_welcome"]
    assert any(m["to"] == "operator.family.welcome.local" for m in welcomes)
