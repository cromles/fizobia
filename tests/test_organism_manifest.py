"""Kurucu manifestosu ve süper organizma testleri."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.main import app
from app.mesh.agent_dialogue import get_dialogue_bus, reset_dialogue_bus
from app.mesh.founder_profile import FOUNDER_NAME
from app.mesh.hierarchy import reset_hierarchy_state
from app.mesh.mission import reset_mission_state
from app.mesh.organism import (
    broadcast_organism_manifest,
    get_organism_status,
    record_mesh_proof_steps,
    reset_organism_state,
)


def _reset():
    reset_dialogue_bus()
    reset_hierarchy_state()
    reset_mission_state()
    reset_organism_state()


def test_manifest_api_yasin_karademir():
    _reset()
    client = TestClient(app)
    body = client.get("/hub/manifest").json()
    assert body["founder"]["founder"] == FOUNDER_NAME
    assert body["current_phase"] == 0
    assert "media" in body["divisions"]
    assert len(body["divisions"]["media"]["agents"]) >= 4


def test_organism_broadcast():
    _reset()
    broadcast_organism_manifest()
    status = get_organism_status()
    assert status["announced"] is True
    msgs = get_dialogue_bus().list_messages(limit=20)
    assert any(m.get("intent") == "founder_manifest" for m in msgs)


def test_agent_governance_scoring():
    _reset()
    steps = [
        {"agent_id": "oam.fetcher.web.local", "worker": "Web-Crawler", "output": {"real_data": True}},
        {"agent_id": "oam.analyst.sentiment.local", "worker": "Sentiment", "output": {"real_data": True}},
    ]
    standings = record_mesh_proof_steps(steps, verdict="ok")
    assert len(standings) == 2
    assert standings[0]["identity_tier"] in ("probation", "active", "core")


def test_ecosystem_shows_founder_and_organism():
    _reset()
    client = TestClient(app)
    body = client.get("/hub/ecosystem").json()
    assert body.get("founder") == FOUNDER_NAME
    assert "organism" in body
    assert body["current_phase"] == 0
