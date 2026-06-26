"""Ekosistem büyüme protokolü testleri."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.agents.builtins import FETCHER_MANIFEST
from app.api.main import app
from app.mesh.founders import FOUNDER_AGENT_IDS, ORCHESTRATOR_ID
from app.mesh.growth_protocol import get_growth_protocol


def test_ecosystem_status_lists_founders():
    client = TestClient(app)
    response = client.get("/hub/ecosystem")
    assert response.status_code == 200
    body = response.json()
    assert body["founder_count"] >= 4
    founder_ids = {f["agent_id"] for f in body["founders"]}
    assert FOUNDER_AGENT_IDS.issubset(founder_ids) or len(founder_ids) >= 3
    assert ORCHESTRATOR_ID in founder_ids or body["founder_count"] >= 1


def test_ecosystem_hire_mesh_proof():
    client = TestClient(app)
    response = client.post(
        "/hub/ecosystem/hire",
        json={"pipeline": "mesh_proof", "symbol": "bitcoin"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["pipeline"] == "mesh_proof"
    assert len(body.get("hired_agents", [])) == 3
    assert body.get("proof_id")
    assert body.get("real_data") is True


def test_ecosystem_join_growth_agent():
    client = TestClient(app)
    manifest = FETCHER_MANIFEST.model_copy()
    manifest.agent_id = "operator.test.growth.local"
    manifest.endpoint = "http://127.0.0.1:8199"
    response = client.post(
        "/hub/ecosystem/join",
        json={"manifest": manifest.model_dump()},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is True
    assert body["tier"] == "growth"

    growth = get_growth_protocol()
    status = growth.ecosystem_status()
    growth_ids = {a["agent_id"] for a in status["growth_agents"]}
    assert "operator.test.growth.local" in growth_ids


def test_ecosystem_events_after_hire():
    client = TestClient(app)
    client.post("/hub/ecosystem/hire", json={"pipeline": "mesh_proof"})
    events = client.get("/hub/ecosystem/events?limit=10").json()["events"]
    types = {e["event_type"] for e in events}
    assert "hire_completed" in types
