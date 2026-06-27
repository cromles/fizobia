"""Runtime durumu — DAG, backpressure, cost ledger, feedback, traces."""

from __future__ import annotations

from typing import Any, Dict

from app.mesh.agent_dag import get_dag_status
from app.mesh.approval_gate import get_approval_status
from app.mesh.backpressure import get_backpressure_status
from app.mesh.cellular_taxonomy import get_cellular_taxonomy
from app.mesh.cost_ledger import get_cost_ledger_status
from app.mesh.decision_trace import get_decision_traces
from app.mesh.feedback import get_feedback_status
from app.mesh.mesh_nervous import get_dag_runtime_status


def get_cellular_organism_status() -> Dict[str, Any]:
    return {
        "cellular": get_cellular_taxonomy(),
        "dag": get_dag_status(),
        "backpressure": get_backpressure_status(),
        "cost_ledger": get_cost_ledger_status(),
        "feedback": get_feedback_status(),
        "approval_gate": get_approval_status(),
        "decision_traces": get_decision_traces(limit=25),
        "runtime": get_dag_runtime_status(),
        # Geriye uyumluluk
        "homeostasis": get_backpressure_status(),
        "metabolism": get_cost_ledger_status(),
        "nervous_system": get_dag_runtime_status(),
    }
