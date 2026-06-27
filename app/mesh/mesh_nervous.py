"""DAG sinyal iletimi — yalnızca şemada tanımlı kenarlar."""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from app.mesh.agent_dag import is_valid_edge, outbound_neighbors
from app.mesh.agent_dialogue import get_dialogue_bus
from app.mesh.cellular_taxonomy import IMMUNE_AGENT_IDS, MUSCLE_AGENT_IDS
from app.mesh.decision_trace import trace_decision
from app.mesh.founders import ORCHESTRATOR_ID

DAG_THREAD_ID = "agent_dag"
_halted_workers: Dict[str, str] = {}


def send_dag_signal(
    from_agent: str,
    to_agent: str,
    text: str,
    *,
    intent: str = "dag_signal",
    payload: Optional[Dict[str, Any]] = None,
    thread_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Sinyal yalnızca DAG kenarı varsa iletilir — geçersiz kenar tanım zamanında yok."""
    if to_agent != "*" and not is_valid_edge(from_agent, to_agent):
        trace_decision(
            "dag_signal_rejected",
            agent_id=from_agent,
            allowed=False,
            reason=f"invalid_edge {from_agent}->{to_agent}",
        )
        return {
            "delivered": False,
            "reason": "invalid_dag_edge",
            "detail": f"{from_agent} → {to_agent} not in DAG schema",
        }
    bus = get_dialogue_bus()
    msg = bus.say(
        from_agent,
        to_agent,
        text,
        intent=intent,
        payload=payload or {},
        thread_id=thread_id or DAG_THREAD_ID,
    )
    return {"delivered": True, "message": msg.to_public()}


# Alias
send_mesh_signal = send_dag_signal


def worker_halt(
    *,
    gate_agent: str,
    target_worker: str,
    reason: str,
) -> Dict[str, Any]:
    if gate_agent not in IMMUNE_AGENT_IDS:
        return {"halted": False, "reason": "not_gate_agent"}
    if target_worker not in MUSCLE_AGENT_IDS:
        return {"halted": False, "reason": "not_muscle_worker"}

    _halted_workers[target_worker] = reason
    halt_id = f"halt_{uuid.uuid4().hex[:8]}"
    signals = [
        send_dag_signal(
            gate_agent,
            ORCHESTRATOR_ID,
            f"WORKER_HALT: {target_worker} — {reason}",
            intent="worker_halt",
            payload={"halt_id": halt_id, "target": target_worker, "reason": reason},
        ),
    ]
    if is_valid_edge(gate_agent, target_worker):
        signals.append(
            send_dag_signal(
                gate_agent,
                target_worker,
                f"Halted: {reason}",
                intent="halt",
                payload={"halt_id": halt_id},
            )
        )
    return {
        "halted": True,
        "halt_id": halt_id,
        "target_worker": target_worker,
        "reason": reason,
        "signals": signals,
    }


immune_halt_muscle = worker_halt


def is_worker_halted(agent_id: str) -> bool:
    return agent_id in _halted_workers


is_muscle_halted = is_worker_halted


def clear_worker_halt(agent_id: str) -> None:
    _halted_workers.pop(agent_id, None)


def broadcast_sensory_to_brain(
    sensory_agent: str,
    signal_text: str,
    *,
    payload: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    delivered: List[Dict[str, Any]] = []
    for target in outbound_neighbors(sensory_agent):
        from app.mesh.cellular_taxonomy import BRAIN_AGENT_IDS

        if target in BRAIN_AGENT_IDS:
            delivered.append(
                send_dag_signal(
                    sensory_agent,
                    target,
                    signal_text,
                    intent="sensory_pulse",
                    payload=payload,
                )
            )
    return delivered


def get_dag_runtime_status() -> Dict[str, Any]:
    from app.mesh.agent_dag import get_dag_status

    bus = get_dialogue_bus()
    return {
        **get_dag_status(),
        "thread_id": DAG_THREAD_ID,
        "halted_workers": dict(_halted_workers),
        "halted_count": len(_halted_workers),
        "recent_signals": bus.list_messages(thread_id=DAG_THREAD_ID, limit=15),
        "updated_at": time.time(),
    }


get_mesh_nervous_status = get_dag_runtime_status


def reset_dag_runtime() -> None:
    _halted_workers.clear()


reset_mesh_nervous = reset_dag_runtime
