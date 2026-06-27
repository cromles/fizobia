"""Hücresel organizma — taxonomy, homeostazi, metabolizma, mesh."""

from fastapi.testclient import TestClient

from app.api.main import app
from app.mesh.cellular_taxonomy import CELLULAR_ORGANISM, CELL_SENSORY, cell_type_for
from app.mesh.feedback import record_failure, reset_feedback, summarize_for_brain
from app.mesh.homeostasis import (
    debit_energy,
    check_pipeline_allowed,
    get_homeostasis_status,
    reset_homeostasis,
)
from app.mesh.mesh_nervous import immune_halt_muscle, is_muscle_halted, reset_mesh_nervous, send_mesh_signal
from app.mesh.metabolism import can_agent_act, record_api_spend, reset_metabolism
from app.workers.market_pulse import AGENT_ID as MARKET_ID
from app.workers.web_crawler import AGENT_ID as WEB_ID


def setup_function() -> None:
    reset_homeostasis()
    reset_metabolism()
    reset_feedback()
    reset_mesh_nervous()


def test_cellular_taxonomy_has_10_agents():
    client = TestClient(app)
    res = client.get("/hub/cellular")
    assert res.status_code == 200
    body = res.json()
    assert body["cellular"]["total_agents"] == 10
    assert len(body["cellular"]["cell_types"]) == 4
    sensory = next(ct for ct in body["cellular"]["cell_types"] if ct["code"] == CELL_SENSORY)
    assert sensory["count"] == 3


def test_mesh_adjacency_not_linear_only():
    assert cell_type_for(WEB_ID) == CELL_SENSORY
    ok = send_mesh_signal(WEB_ID, "oam.expert.macro.local", "sinyal test")
    assert ok["delivered"] is True
    bad = send_mesh_signal(WEB_ID, MARKET_ID, "doğrudan kas yasak değil ama komşu değilse red")
    assert bad["delivered"] is False or bad.get("reason") == "mesh_reject"


def test_homeostasis_hunt_blocks_heavy_pipeline():
    status = get_homeostasis_status()
    assert status["mode"] == "normal"
    debit_energy(22.0)
    mode = get_homeostasis_status()["mode"]
    assert mode in ("hunt", "conserve", "critical")
    allowed, _ = check_pipeline_allowed("arena")
    assert allowed is False


def test_immune_halt_muscle():
    halt = immune_halt_muscle(
        immune_agent="oam.critic.immune.local",
        target_muscle=MARKET_ID,
        reason="test audit fail",
    )
    assert halt["halted"] is True
    assert is_muscle_halted(MARKET_ID)


def test_metabolism_starvation_blocks_muscle():
    for _ in range(12):
        record_api_spend(MARKET_ID)
    ok, reason = can_agent_act(MARKET_ID)
    assert ok is False
    assert "açlık" in reason or "Homeostazi" in reason or "kısıtlı" in reason


def test_feedback_brain_summary():
    record_failure(agent_id="oam.orchestrator.pipeline.local", error="kod hatası", pipeline="goal")
    assert "kod hatası" in summarize_for_brain()


def test_cellular_agent_count_constant():
    assert len(CELLULAR_ORGANISM) == 10
