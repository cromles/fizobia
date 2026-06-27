"""Runtime mimari — DAG, backpressure, cost ledger, structured feedback."""

from fastapi.testclient import TestClient

from app.api.main import app
from app.mesh.agent_dag import AGENT_DAG_EDGES, is_valid_edge
from app.mesh.approval_gate import check_approval, grant_approval, reset_approval_gate
from app.mesh.backpressure import (
    check_pipeline_allowed,
    debit_budget,
    get_backpressure_status,
    health_score,
    reset_backpressure,
    throttle_factor,
)
from app.mesh.cost_ledger import can_worker_run, record_cost, reset_cost_ledger
from app.mesh.decision_trace import get_decision_traces, reset_decision_traces
from app.mesh.feedback import (
    classify_error,
    get_coordinator_actions,
    record_feedback,
    reset_feedback,
    should_skip_pipeline,
)
from app.mesh.mesh_nervous import reset_dag_runtime, send_dag_signal, worker_halt
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


def test_dag_edges_only_valid_nodes():
    for src, dst in AGENT_DAG_EDGES:
        assert is_valid_edge(src, dst)


def test_dag_rejects_undefined_edge_at_runtime():
    bad = send_dag_signal(WEB_ID, MARKET_ID, "invalid hop")
    assert bad["delivered"] is False
    assert bad["reason"] == "invalid_dag_edge"
    traces = get_decision_traces(limit=5)
    assert any(t["decision"] == "dag_signal_rejected" for t in traces)


def test_dag_accepts_schema_edge():
    ok = send_dag_signal(WEB_ID, MACRO_ID, "valid")
    assert ok["delivered"] is True


def test_backpressure_smooth_throttle_not_step_modes():
    assert health_score() == 1.0
    assert throttle_factor() == 1.0
    debit_budget(12.0)
    h1 = health_score()
    assert 0.45 < h1 < 0.55
    debit_budget(8.0)
    h2 = health_score()
    tf2 = throttle_factor()
    assert h2 < h1
    assert tf2 < 1.0


def test_low_health_blocks_arena_with_trace():
    debit_budget(24.0)
    allowed, reason = check_pipeline_allowed("arena")
    assert allowed is False
    assert "approval" in reason or "backpressure" in reason or "budget_exhausted" in reason
    traces = get_decision_traces(limit=3)
    assert traces[0]["allowed"] is False


def test_approval_gate_separate_from_throttle():
    debit_budget(24.5)
    ok, reason = check_approval()
    assert ok is False
    assert "approval_required" in reason
    grant_approval(operator="test")
    ok2, _ = check_approval()
    assert ok2 is True
    allowed, reason = check_pipeline_allowed("mesh_proof")
    assert allowed is True


def test_cost_ledger_budget_exhausted_naming():
    for _ in range(12):
        record_cost(MARKET_ID, operation="api_call", success=True)
    ok, reason = can_worker_run(MARKET_ID)
    assert ok is False
    assert "budget_exhausted" in reason


def test_structured_feedback_rate_limit_rule():
    agent = "oam.orchestrator.pipeline.local"
    for _ in range(3):
        record_feedback(
            agent_id=agent,
            pipeline="mesh_proof",
            success=False,
            error="429 rate limit",
            http_status=429,
        )
    skip, reason = should_skip_pipeline(agent, "mesh_proof")
    assert skip is True
    assert "rate_limit" in reason
    actions = get_coordinator_actions()
    assert any(a["action"] == "skip_pipeline" for a in actions)


def test_classify_error_types():
    assert classify_error("timeout", None) == "timeout"
    assert classify_error("429 too many", 429) == "rate_limit"
    assert classify_error("bad request", 400) == "client_4xx"


def test_hub_cellular_observability_fields():
    client = TestClient(app)
    res = client.get("/hub/cellular")
    assert res.status_code == 200
    body = res.json()
    assert "backpressure" in body
    assert "cost_ledger" in body
    assert "decision_traces" in body
    assert "dag" in body
    assert body["dag"]["topology"] == "dag"
    assert "health_score" in body["backpressure"]


def test_hub_workers_dag_topology():
    client = TestClient(app)
    body = client.get("/hub/workers").json()
    assert body["topology"] == "dag"
    assert body["count"] == 10


def test_worker_halt():
    halt = worker_halt(
        gate_agent="oam.critic.immune.local",
        target_worker=MARKET_ID,
        reason="audit fail",
    )
    assert halt["halted"] is True
