"""Hücresel runtime — geriye uyumluluk testleri."""

from app.mesh.cellular_taxonomy import CELLULAR_ORGANISM, CELL_SENSORY, cell_type_for
from app.mesh.agent_dag import is_valid_edge
from app.mesh.approval_gate import reset_approval_gate
from app.mesh.backpressure import debit_budget, reset_backpressure
from app.mesh.cost_ledger import record_cost, reset_cost_ledger
from app.mesh.decision_trace import reset_decision_traces
from app.mesh.feedback import record_feedback, reset_feedback
from app.mesh.mesh_nervous import reset_dag_runtime, send_dag_signal, worker_halt
from app.mesh.cost_ledger import can_worker_run
from app.mesh.backpressure import check_pipeline_allowed, health_score
from app.workers.macro_strategist import AGENT_ID as MACRO_ID
from app.workers.market_pulse import AGENT_ID as MARKET_ID
from app.workers.web_crawler import AGENT_ID as WEB_ID


def setup_function() -> None:
    reset_backpressure()
    reset_cost_ledger()
    reset_feedback()
    reset_dag_runtime()
    reset_decision_traces()
    reset_approval_gate()


def test_cellular_agent_count_constant():
    assert len(CELLULAR_ORGANISM) == 10


def test_dag_not_undirected_mesh():
    assert cell_type_for(WEB_ID) == CELL_SENSORY
    assert is_valid_edge(WEB_ID, MACRO_ID)
    assert not is_valid_edge(WEB_ID, MARKET_ID)


def test_backpressure_blocks_heavy_pipeline():
    assert health_score() == 1.0
    debit_budget(22.0)
    allowed, _ = check_pipeline_allowed("arena")
    assert allowed is False


def test_worker_halt():
    halt = worker_halt(
        gate_agent="oam.critic.immune.local",
        target_worker=MARKET_ID,
        reason="test",
    )
    assert halt["halted"] is True


def test_budget_exhausted_blocks_worker():
    for _ in range(12):
        record_cost(MARKET_ID)
    ok, reason = can_worker_run(MARKET_ID)
    assert ok is False
    assert "budget_exhausted" in reason


def test_structured_feedback_not_plain_summary():
    record_feedback(
        agent_id="oam.orchestrator.pipeline.local",
        pipeline="goal",
        success=False,
        error="runtime",
        http_status=500,
    )
    from app.mesh.feedback import get_feedback_status

    status = get_feedback_status()
    assert status["records"][0]["error_type"] == "upstream_5xx"
