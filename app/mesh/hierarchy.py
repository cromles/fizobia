"""Axium komuta zinciri — Kurucu → Baş Yardımcı → Koordinatör → İşçi ajanlar."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from app.mesh.agent_dialogue import get_dialogue_bus
from app.mesh.founders import FOUNDER_ROLES, ORCHESTRATOR_ID, ORCHESTRATOR_NAME
from app.protocol.schemas import AgentManifest

FOUNDER_OPERATOR_ID = "oam.founder.operator"
FOUNDER_OPERATOR_NAME = "Kurucu Operatör"

ASSISTANT_ID = "oam.assistant.chief.local"
ASSISTANT_NAME = "Axium Baş Yardımcı"

HIERARCHY_THREAD_ID = "hierarchy_chain"

CHAIN_OF_COMMAND: List[Dict[str, Any]] = [
    {
        "tier": 0,
        "role": "founder",
        "agent_id": FOUNDER_OPERATOR_ID,
        "display_name": FOUNDER_OPERATOR_NAME,
        "reports_to": None,
        "mission": "Vizyonu belirler — durmayız, hızlanırız, boşluğu doldururuz.",
    },
    {
        "tier": 1,
        "role": "chief_assistant",
        "agent_id": ASSISTANT_ID,
        "display_name": ASSISTANT_NAME,
        "reports_to": FOUNDER_OPERATOR_ID,
        "mission": "Kurucunun yardımcısı — emirleri mesh'e çevirir, koordinatöre iletir.",
    },
    {
        "tier": 2,
        "role": "coordinator",
        "agent_id": ORCHESTRATOR_ID,
        "display_name": ORCHESTRATOR_NAME,
        "reports_to": ASSISTANT_ID,
        "mission": "Baş yardımcının sağ kolu — ajan işe alır, pipeline açar, tempo tutar.",
    },
    {
        "tier": 3,
        "role": "worker_pool",
        "agent_id": "oam.mesh.workers",
        "display_name": "İşçi Ajanlar",
        "reports_to": ORCHESTRATOR_ID,
        "mission": "Baş yardımcının ekibi — veri, sentiment, piyasa, zincir; ne gerekiyorsa yapar.",
    },
]

_last_command: Optional[Dict[str, Any]] = None
_chain_announced = False


def tier_for_agent(agent_id: str) -> Optional[Dict[str, Any]]:
    for entry in CHAIN_OF_COMMAND:
        if entry["agent_id"] == agent_id:
            return entry
    if agent_id in FOUNDER_ROLES:
        return {
            "tier": 3,
            "role": "worker",
            "agent_id": agent_id,
            "display_name": FOUNDER_ROLES[agent_id].display_name,
            "reports_to": ORCHESTRATOR_ID,
        }
    return {
        "tier": 3,
        "role": "growth_worker",
        "agent_id": agent_id,
        "display_name": agent_id,
        "reports_to": ORCHESTRATOR_ID,
    }


def get_hierarchy_status(
    agents: Optional[List[AgentManifest]] = None,
) -> Dict[str, Any]:
    """Hub için komuta zinciri özeti."""
    bus = get_dialogue_bus()
    thread_msgs = bus.list_messages(thread_id=HIERARCHY_THREAD_ID, limit=30)
    worker_count = len(agents) if agents else 0
    return {
        "chain": CHAIN_OF_COMMAND,
        "motto": "Kurucu → Baş Yardımcı → Koordinatör → İşçiler",
        "thread_id": HIERARCHY_THREAD_ID,
        "announced": _chain_announced,
        "last_command": _last_command,
        "worker_count": worker_count,
        "recent_orders": thread_msgs[:10],
    }


def announce_chain_of_command(*, force: bool = False) -> Dict[str, Any]:
    """Komuta zincirini diyalog bus üzerinden ilan et."""
    global _chain_announced

    if _chain_announced and not force:
        return get_hierarchy_status()

    bus = get_dialogue_bus()
    bus.broadcast(
        FOUNDER_OPERATOR_ID,
        (
            "Axium komuta zinciri aktif: Ben kurucuyum. Baş yardımcım emirleri mesh'e taşır; "
            "koordinatör işe alır; işçiler ne gerekiyorsa yapar. Durmayacağız."
        ),
        intent="hierarchy_charter",
        thread_id=HIERARCHY_THREAD_ID,
    )
    bus.say(
        FOUNDER_OPERATOR_ID,
        ASSISTANT_ID,
        "Sen benim baş yardımcımsın — kurucu emirlerini koordinatöre ilet, mesh'i hızlandır.",
        intent="hierarchy_delegate",
        thread_id=HIERARCHY_THREAD_ID,
    )
    bus.say(
        ASSISTANT_ID,
        ORCHESTRATOR_ID,
        "Koordinatör: işçi ajanları işe al, mesh proof ve görevleri durmadan çalıştır.",
        intent="hierarchy_order",
        thread_id=HIERARCHY_THREAD_ID,
    )
    bus.say(
        ORCHESTRATOR_ID,
        "oam.mesh.workers",
        "İşçi ekip: kurucu ve baş yardımcının emriyle hareket edin — ne gerekiyorsa yapın.",
        intent="hierarchy_order",
        thread_id=HIERARCHY_THREAD_ID,
    )

    _chain_announced = True
    return get_hierarchy_status()


def record_founder_command(
    command: str,
    *,
    message: str = "",
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Kurucu emri → baş yardımcı → koordinatör zinciri."""
    global _last_command

    bus = get_dialogue_bus()
    text = message or command
    founder_msg = bus.say(
        FOUNDER_OPERATOR_ID,
        ASSISTANT_ID,
        f"Kurucu emri: {text}",
        intent="founder_command",
        payload={"command": command, **(payload or {})},
        thread_id=HIERARCHY_THREAD_ID,
    )
    assistant_msg = bus.say(
        ASSISTANT_ID,
        ORCHESTRATOR_ID,
        f"Emri aldım — koordinatöre iletiyorum: {text}",
        intent="assistant_delegate",
        payload={"command": command},
        thread_id=HIERARCHY_THREAD_ID,
    )
    orch_msg = bus.say(
        ORCHESTRATOR_ID,
        "oam.mesh.workers",
        f"İşçiler hazır olun: {text}",
        intent="coordinator_dispatch",
        payload={"command": command},
        thread_id=HIERARCHY_THREAD_ID,
    )

    _last_command = {
        "command": command,
        "message": text,
        "timestamp": time.time(),
        "chain": [founder_msg.to_public(), assistant_msg.to_public(), orch_msg.to_public()],
    }
    return _last_command


def autopilot_cycle_order(cycle: int, *, symbol: str = "bitcoin") -> Dict[str, Any]:
    """Otopilot döngüsü — kurucu hızlan emri simülasyonu."""
    return record_founder_command(
        "autopilot_mesh_proof",
        message=f"Otopilot döngü #{cycle}: {symbol} mesh proof — durma, hızlan.",
        payload={"cycle": cycle, "symbol": symbol, "source": "autopilot"},
    )


def reset_hierarchy_state() -> None:
    global _chain_announced, _last_command
    _chain_announced = False
    _last_command = None
