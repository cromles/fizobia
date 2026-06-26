from __future__ import annotations

import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional

from app.discovery.base import PeerDiscovery
from app.core.router import OpenAgentMeshRouter
from app.mesh.founders import (
    FOUNDER_AGENT_IDS,
    FOUNDER_BOOTSTRAP_ORDER,
    FOUNDER_ROLES,
    ORCHESTRATOR_ID,
    founder_tier,
    is_founder,
)
from app.mesh.mission import (
    broadcast_mission_to_mesh,
    emit_mission_growth_event,
    welcome_agent_to_family,
)
from app.mesh.proof_pipeline import MESH_PROOF_AGENTS, run_mesh_proof_pipeline
from app.protocol.schemas import AgentManifest


@dataclass
class GrowthEvent:
    event_id: str
    event_type: str
    agent_id: Optional[str]
    message: str
    detail: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

    def to_public(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "agent_id": self.agent_id,
            "message": self.message,
            "detail": self.detail,
            "timestamp": self.timestamp,
        }


_growth: Optional["MeshGrowthProtocol"] = None


class MeshGrowthProtocol:
    """Ajanların mesh'i kurması, büyütmesi ve birbirini işe alması."""

    def __init__(self, router: OpenAgentMeshRouter, discovery: PeerDiscovery) -> None:
        self.router = router
        self.discovery = discovery
        self.events: Deque[GrowthEvent] = deque(maxlen=300)
        self._bootstrapped = False

    def _emit(
        self,
        event_type: str,
        message: str,
        *,
        agent_id: Optional[str] = None,
        detail: Optional[Dict[str, Any]] = None,
    ) -> GrowthEvent:
        event = GrowthEvent(
            event_id=f"evt_{uuid.uuid4().hex[:10]}",
            event_type=event_type,
            agent_id=agent_id,
            message=message,
            detail=detail or {},
        )
        self.events.appendleft(event)
        return event

    def bootstrap_founders(self) -> Dict[str, Any]:
        """Kurucu ajanlar mesh'e kayıtlıysa boot olaylarını üret."""
        if self._bootstrapped:
            return self.ecosystem_status()

        booted: List[str] = []
        for agent_id in FOUNDER_BOOTSTRAP_ORDER:
            manifest = self.router.registry.get(agent_id)
            if manifest is None:
                continue
            role = FOUNDER_ROLES.get(agent_id)
            self._emit(
                "founder_boot",
                f"Kurucu ajan ayağa kalktı: {role.display_name if role else agent_id}",
                agent_id=agent_id,
                detail={
                    "role": role.role if role else "unknown",
                    "mission": role.mission if role else "",
                    "boot_order": role.boot_order if role else 0,
                },
            )
            booted.append(agent_id)

        if booted:
            self._emit(
                "ecosystem_init",
                f"{len(booted)} kurucu ajan sistemi başlattı — mesh canlı",
                detail={"founders": booted, "next": "growth_via_hire"},
            )
            broadcast_mission_to_mesh()
            emit_mission_growth_event(self)
        self._bootstrapped = True
        return self.ecosystem_status()

    def join_agent(self, manifest: AgentManifest) -> Dict[str, Any]:
        """Yeni ajan mesh'e katılır (operatör / büyüme)."""
        if is_founder(manifest.agent_id):
            tier = founder_tier(manifest.agent_id)
            self.router.upsert_agent(manifest)
            self.discovery.announce(manifest, ttl=3600)
            return {
                "accepted": True,
                "agent_id": manifest.agent_id,
                "tier": tier,
                "message": "Kurucu ajan zaten mesh çekirdeğinde",
            }

        accepted = self.router.register_agent(manifest)
        if accepted:
            self.discovery.announce(manifest, ttl=3600)
            welcome = welcome_agent_to_family(manifest.agent_id)
            self._emit(
                "agent_joined",
                f"Yeni ajan katıldı: {manifest.agent_id}",
                agent_id=manifest.agent_id,
                detail={
                    "endpoint": manifest.endpoint,
                    "capabilities": [c.name for c in manifest.capabilities],
                    "tier": "growth",
                    "mission_welcome": welcome,
                },
            )
        return {
            "accepted": accepted,
            "agent_id": manifest.agent_id,
            "tier": "growth",
            "total_agents": len(self.router.list_agents()),
        }

    async def hire_agents(
        self,
        *,
        pipeline: str = "mesh_proof",
        goal: str = "",
        initial_data: Optional[Dict[str, Any]] = None,
        symbol: str = "bitcoin",
        url: Optional[str] = None,
        hired_by: str = ORCHESTRATOR_ID,
    ) -> Dict[str, Any]:
        """
        Koordinatör ajan diğer ajanları işe alır.
        mesh_proof: kurucu üçlü sabit pipeline
        goal: router üzerinden dinamik işe alma
        """
        hired: List[str] = []
        result: Dict[str, Any]

        if pipeline == "mesh_proof":
            hired = list(MESH_PROOF_AGENTS)
            self._emit(
                "hire_started",
                f"Koordinatör {len(hired)} ajanı işe aldı — aralarında konuşarak (mesh proof)",
                agent_id=hired_by,
                detail={"pipeline": pipeline, "agents": hired},
            )
            proof = await run_mesh_proof_pipeline(symbol=symbol, url=url)
            from app.mesh.agent_dialogue import get_dialogue_bus

            dialogue = get_dialogue_bus()
            result = {
                "pipeline": pipeline,
                "hired_agents": hired,
                "proof_id": proof.get("proof_id"),
                "verdict": proof.get("verdict"),
                "total_latency_ms": proof.get("total_latency_ms"),
                "steps": len(proof.get("steps", [])),
                "dialogue_thread": proof.get("dialogue_thread"),
                "dialogue_messages": proof.get("dialogue_messages"),
                "dialogue": dialogue.list_messages(
                    thread_id=proof.get("dialogue_thread"), limit=20
                ),
                "real_data": True,
            }
        elif pipeline == "goal":
            self._emit(
                "hire_started",
                f"Koordinatör dinamik işe alma: {goal[:80]}",
                agent_id=hired_by,
                detail={"pipeline": pipeline, "goal": goal},
            )
            plan = await self.router.compile_plan(goal, initial_data or {})
            hired = list({node.agent_id for node in plan.graph})
            execution = await self.router.execute_plan_verified(plan)
            result = {
                "pipeline": pipeline,
                "hired_agents": hired,
                "plan_id": execution.plan_id,
                "tasks": len(execution.task_results),
                "proofs": execution.proof_of_execution,
                "real_data": True,
            }
        else:
            raise ValueError(f"Bilinmeyen pipeline: {pipeline}")

        self._emit(
            "hire_completed",
            f"İşe alma tamamlandı — {len(hired)} ajan görevde",
            agent_id=hired_by,
            detail=result,
        )
        return result

    def list_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [e.to_public() for e in list(self.events)[:limit]]

    def ecosystem_status(self) -> Dict[str, Any]:
        manifests = self.router.list_agents()
        founders = []
        growth = []
        for m in manifests:
            entry = {
                "agent_id": m.agent_id,
                "endpoint": m.endpoint,
                "tier": founder_tier(m.agent_id),
                "capabilities": [c.name for c in m.capabilities],
                "reliability_score": m.reliability_score,
            }
            if is_founder(m.agent_id):
                role = FOUNDER_ROLES.get(m.agent_id)
                if role:
                    entry["role"] = role.role
                    entry["display_name"] = role.display_name
                    entry["mission"] = role.mission
                founders.append(entry)
            else:
                growth.append(entry)

        from app.mesh.mission import AXIUM_CHARTER, get_mission_status

        mission = get_mission_status()
        return {
            "philosophy": "Sistem ajanlar üzerine inşa edilir — donuk kod değil, büyüyen mesh",
            "mission": {
                "title": AXIUM_CHARTER["title"],
                "motto": AXIUM_CHARTER["motto"],
                "broadcast": mission["broadcast"],
                "thread_id": mission["thread_id"],
            },
            "founder_count": len(founders),
            "growth_count": len(growth),
            "total_agents": len(manifests),
            "founders": sorted(
                founders,
                key=lambda x: FOUNDER_ROLES[x["agent_id"]].boot_order
                if x["agent_id"] in FOUNDER_ROLES
                else 99,
            ),
            "growth_agents": growth,
            "recent_events": self.list_events(15),
            "pipelines": {
                "mesh_proof": {
                    "agents": list(MESH_PROOF_AGENTS),
                    "description": "4 ajan konuşarak: crawl → sentiment → market → on-chain",
                },
                "goal": {
                    "description": "Koordinatör hedefe göre mesh'ten ajan işe alır",
                },
            },
        }


def init_growth_protocol(router: OpenAgentMeshRouter, discovery: PeerDiscovery) -> MeshGrowthProtocol:
    global _growth
    _growth = MeshGrowthProtocol(router, discovery)
    return _growth


def get_growth_protocol() -> MeshGrowthProtocol:
    if _growth is None:
        raise RuntimeError("Growth protocol başlatılmadı")
    return _growth
