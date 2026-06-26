"""Ekosistem birleştirme testleri."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.mesh.agent_dialogue import reset_dialogue_bus
from app.mesh.assembly_pipeline import run_ecosystem_assembly
from app.mesh.ecosystem_registry import ECOSYSTEM_ASSEMBLY_AGENTS, ECOSYSTEM_STACK_AGENT_IDS
from app.mesh.hierarchy import reset_hierarchy_state
from app.mesh.mission import reset_mission_state
from app.mesh.organism import reset_organism_state


@pytest.fixture(autouse=True)
def _reset():
    reset_dialogue_bus()
    reset_hierarchy_state()
    reset_mission_state()
    reset_organism_state()
    yield


def test_ecosystem_stack_agent_count():
    assert len(ECOSYSTEM_STACK_AGENT_IDS) == 10


@pytest.mark.asyncio
async def test_assembly_pipeline_mocked():
    proof = {
        "proof_id": "proof_asm1",
        "verdict": "bullish",
        "total_latency_ms": 200,
        "steps": [
            {"output": {"headline": "BTC up", "real_data": True}},
            {"output": {"sentiment": "bullish", "real_data": True}},
            {"output": {"price_usd": 90000, "real_data": True}},
            {"output": {"real_data": True}},
        ],
        "dialogue_thread": "proof_x",
    }
    with patch("app.mesh.assembly_pipeline.run_mesh_proof_pipeline", AsyncMock(return_value=proof)):
        result = await run_ecosystem_assembly(symbol="bitcoin")

    assert result["assembly_id"]
    assert result["story"]["headline"]
    assert result["brand"]["social_post"]
    assert result["outreach"]["pitch"]
    assert result["share_card"]["share_card"]
    assert result["capital_signal"]["readiness"]
    assert result["assembly_steps"] == 5


def test_ecosystem_assemble_endpoint_mocked():
    client = TestClient(app)
    mock_body = {
        "pipeline": "ecosystem_assembly",
        "assembly_id": "asm_test",
        "proof_id": "p1",
        "hired_agents": list(ECOSYSTEM_ASSEMBLY_AGENTS),
        "real_data": True,
    }
    with patch(
        "app.mesh.growth_protocol.run_ecosystem_assembly",
        AsyncMock(
            return_value={
                "assembly_id": "asm_test",
                "proof_id": "p1",
                "mesh_verdict": "ok",
                "steps": [],
                "story": {"headline": "h"},
                "share_card": {"share_card": "c"},
                "capital_signal": {"readiness": "bootstrap"},
                "dialogue_thread": "t1",
                "dialogue_messages": 3,
                "total_latency_ms": 100,
                "assembly_steps": 5,
            }
        ),
    ):
        response = client.post("/hub/ecosystem/assemble", json={"symbol": "bitcoin"})
    assert response.status_code == 200
    body = response.json()
    assert body["pipeline"] == "ecosystem_assembly"
    assert len(body.get("hired_agents", [])) == len(ECOSYSTEM_ASSEMBLY_AGENTS)


def test_extended_manifests_include_media():
    from app.agents.extended_builtins import EXTENDED_MANIFESTS

    ids = {m.agent_id for m in EXTENDED_MANIFESTS}
    assert "oam.media.story.local" in ids
    assert "oam.capital.fundraise.local" in ids
