"""Mesh sinir sistemi — ağ topolojisi, bağışıklık durdurma sinyali."""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from app.mesh.agent_dialogue import get_dialogue_bus
from app.mesh.cellular_taxonomy import (
    IMMUNE_AGENT_IDS,
    MESH_ADJACENCY,
    MUSCLE_AGENT_IDS,
    is_mesh_neighbor,
)
from app.mesh.founders import ORCHESTRATOR_ID

MESH_THREAD_ID = "cellular_mesh"
_halted_muscles: Dict[str, str] = {}


def send_mesh_signal(
    from_agent: str,
    to_agent: str,
    text: str,
    *,
    intent: str = "mesh_signal",
    payload: Optional[Dict[str, Any]] = None,
    thread_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Mesh sinaps — komşu olmayan hücrelere doğrudan mesaj yok (fabrika bandı değil)."""
    if to_agent != "*" and not is_mesh_neighbor(from_agent, to_agent):
        return {
            "delivered": False,
            "reason": "mesh_reject",
            "detail": f"{from_agent} → {to_agent} sinaps yok",
        }
    bus = get_dialogue_bus()
    msg = bus.say(
        from_agent,
        to_agent,
        text,
        intent=intent,
        payload=payload or {},
        thread_id=thread_id or MESH_THREAD_ID,
    )
    return {"delivered": True, "message": msg.to_public()}


def immune_halt_muscle(
    *,
    immune_agent: str,
    target_muscle: str,
    reason: str,
) -> Dict[str, Any]:
    """Bağışıklık hücresi kası durdurur — mesh üzerinden."""
    if immune_agent not in IMMUNE_AGENT_IDS:
        return {"halted": False, "reason": "not_immune_cell"}
    if target_muscle not in MUSCLE_AGENT_IDS:
        return {"halted": False, "reason": "not_muscle_cell"}

    _halted_muscles[target_muscle] = reason
    bus = get_dialogue_bus()
    halt_id = f"halt_{uuid.uuid4().hex[:8]}"

    to_orch = send_mesh_signal(
        immune_agent,
        ORCHESTRATOR_ID,
        f"KAS DURDUR: {target_muscle} — {reason}",
        intent="immune_halt",
        payload={"halt_id": halt_id, "target": target_muscle, "reason": reason},
    )
    to_muscle = send_mesh_signal(
        immune_agent,
        target_muscle,
        f"Durduruldu: {reason}",
        intent="halt",
        payload={"halt_id": halt_id},
    )
    bus.broadcast(
        immune_agent,
        f"Bağışıklık müdahalesi — {target_muscle} askıya alındı.",
        intent="immune_alert",
        thread_id=MESH_THREAD_ID,
    )
    return {
        "halted": True,
        "halt_id": halt_id,
        "target_muscle": target_muscle,
        "reason": reason,
        "signals": [to_orch, to_muscle],
    }


def is_muscle_halted(agent_id: str) -> bool:
    return agent_id in _halted_muscles


def clear_muscle_halt(agent_id: str) -> None:
    _halted_muscles.pop(agent_id, None)


def broadcast_sensory_to_brain(
    sensory_agent: str,
    signal_text: str,
    *,
    payload: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Duyu hücresi beyin havuzuna paralel mesh yayını (doğrusal değil)."""
    from app.mesh.cellular_taxonomy import BRAIN_AGENT_IDS

    delivered: List[Dict[str, Any]] = []
    for brain_id in BRAIN_AGENT_IDS:
        if is_mesh_neighbor(sensory_agent, brain_id):
            delivered.append(
                send_mesh_signal(
                    sensory_agent,
                    brain_id,
                    signal_text,
                    intent="sensory_pulse",
                    payload=payload,
                )
            )
    return delivered


def get_mesh_nervous_status() -> Dict[str, Any]:
    bus = get_dialogue_bus()
    return {
        "topology": "mesh_network",
        "thread_id": MESH_THREAD_ID,
        "adjacency_count": len(MESH_ADJACENCY),
        "halted_muscles": dict(_halted_muscles),
        "halted_count": len(_halted_muscles),
        "recent_mesh_messages": bus.list_messages(thread_id=MESH_THREAD_ID, limit=15),
        "immune_agents": list(IMMUNE_AGENT_IDS),
        "updated_at": time.time(),
    }


def reset_mesh_nervous() -> None:
    _halted_muscles.clear()
