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
from app.mesh.founder_profile import FOUNDER_NAME
from app.mesh.hierarchy import announce_chain_of_command
from app.mesh.organism import broadcast_organism_manifest, filter_eligible_agents, record_mesh_proof_steps
from app.mesh.mission import (
    broadcast_mission_to_mesh,
    emit_mission_growth_event,
    welcome_agent_to_family,
)
from app.mesh.assembly_pipeline import run_ecosystem_assembly
from app.mesh.arena_pipeline import run_arena_pipeline
from app.mesh.ecosystem_registry import ECOSYSTEM_ASSEMBLY_AGENTS, MEDIA_AGENT_IDS_SET
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
            announce_chain_of_command()
            broadcast_organism_manifest()
            self._emit(
                "organism_manifest",
                f"Kurucu manifestosu yayınlandı — {FOUNDER_NAME}",
                detail={"phase": 0, "focus": "capital_and_zero_exit"},
            )
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
            hired = filter_eligible_agents(list(MESH_PROOF_AGENTS))
            culled = [a for a in MESH_PROOF_AGENTS if a not in hired]
            if culled:
                self._emit(
                    "agent_culled_skip",
                    f"Elenen ajanlar pipeline dışı: {', '.join(culled)}",
                    detail={"culled": culled, "pipeline": pipeline},
                )
            if not hired:
                raise ValueError("Tüm mesh proof ajanları elendi — pipeline çalıştırılamaz")
            self._emit(
                "hire_started",
                f"Koordinatör {len(hired)} ajanı işe aldı — aralarında konuşarak (mesh proof)",
                agent_id=hired_by,
                detail={"pipeline": pipeline, "agents": hired},
            )
            proof = await run_mesh_proof_pipeline(symbol=symbol, url=url)
            from app.mesh.agent_dialogue import get_dialogue_bus

            dialogue = get_dialogue_bus()
            standings = record_mesh_proof_steps(
                proof.get("steps", []),
                verdict=proof.get("verdict", ""),
            )
            for row in standings:
                change = row.get("tier_change")
                if not change:
                    continue
                self._emit(
                    "agent_tier_changed",
                    f"{change['agent_id']}: {change['from_tier']} → {change['to_tier']}",
                    agent_id=change["agent_id"],
                    detail=change,
                )
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
                "agent_standings": standings,
                "real_data": True,
            }
        elif pipeline == "ecosystem_assembly":
            hired = filter_eligible_agents(list(ECOSYSTEM_ASSEMBLY_AGENTS))
            self._emit(
                "hire_started",
                f"Ekosistem birleştirme — {len(hired)} ajan (mesh + medya + sermaye)",
                agent_id=hired_by,
                detail={"pipeline": pipeline, "agents": hired},
            )
            from app.investment.factory import get_investment_hub
            from app.mesh.agent_dialogue import get_dialogue_bus

            hub = get_investment_hub()
            cards = hub.list_identity_cards(self.router.list_agents())
            stats: Dict[str, Any] = {
                "total_revenue_usd": sum(c.finance.total_revenue_usd for c in cards),
                "tvl_usd": sum(c.finance.staking_pool_tvl_usd for c in cards),
                "total_agents": len(cards),
                "mesh_proofs": 0,
            }
            try:
                from app.mesh.proof_vault import get_proof_vault

                stats["mesh_proofs"] = get_proof_vault().stats().get("proofs_recorded", 0)
            except Exception:
                pass

            assembly = await run_ecosystem_assembly(symbol=symbol, url=url, hub_stats=stats)
            dialogue = get_dialogue_bus()
            standings = record_mesh_proof_steps(
                assembly.get("steps", []),
                verdict=assembly.get("mesh_verdict", ""),
            )
            result = {
                "pipeline": pipeline,
                "hired_agents": hired,
                "assembly_id": assembly.get("assembly_id"),
                "proof_id": assembly.get("proof_id"),
                "verdict": assembly.get("mesh_verdict"),
                "story_headline": assembly.get("story", {}).get("headline"),
                "share_card": assembly.get("share_card", {}).get("share_card"),
                "capital_readiness": assembly.get("capital_signal", {}).get("readiness"),
                "total_latency_ms": assembly.get("total_latency_ms"),
                "steps": assembly.get("assembly_steps"),
                "dialogue_thread": assembly.get("dialogue_thread"),
                "dialogue_messages": assembly.get("dialogue_messages"),
                "dialogue": dialogue.list_messages(
                    thread_id=assembly.get("dialogue_thread"), limit=25
                ),
                "agent_standings": standings,
                "real_data": True,
            }
        elif pipeline == "arena":
            prompt = goal or str((initial_data or {}).get("prompt", ""))
            if len(prompt.strip()) < 8:
                raise ValueError("Arena pipeline için prompt gerekli (goal veya initial_data.prompt)")
            self._emit(
                "arena_started",
                f"Gladyatör arenası — {prompt[:60]}…",
                agent_id=hired_by,
                detail={"pipeline": pipeline},
            )
            arena = await run_arena_pipeline(
                user_prompt=prompt,
                background_music=bool((initial_data or {}).get("background_music", True)),
                duration_sec=int((initial_data or {}).get("duration_sec", 30)),
            )
            hired = arena.get("arena", {}).get("competitors", [])
            from app.mesh.agent_dialogue import get_dialogue_bus

            dialogue = get_dialogue_bus()
            standings = record_mesh_proof_steps(
                [
                    {
                        "agent_id": arena["winner"]["agent_id"],
                        "worker": arena["winner"].get("display_name", ""),
                        "output": {"real_data": True},
                    }
                ],
                verdict="arena_win",
            )
            result = {
                "pipeline": pipeline,
                "hired_agents": hired,
                "job_id": arena.get("job_id"),
                "winner": arena.get("winner"),
                "render": arena.get("render"),
                "audit": arena.get("arena", {}).get("audit"),
                "total_latency_ms": arena.get("total_latency_ms"),
                "dialogue_thread": arena.get("dialogue_thread"),
                "dialogue_messages": arena.get("dialogue_messages"),
                "dialogue": dialogue.list_messages(
                    thread_id=arena.get("dialogue_thread"), limit=25
                ),
                "agent_standings": standings,
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

        from app.mesh.hierarchy import get_hierarchy_status
        from app.mesh.mission import AXIUM_CHARTER, get_mission_status
        from app.mesh.organism import get_organism_status

        mission = get_mission_status()
        hierarchy = get_hierarchy_status(manifests)
        organism = get_organism_status()
        return {
            "philosophy": "Süper organizma — her ajan bütünün parçası; bahane yok, kısa yol var",
            "founder": organism["founder"]["founder"],
            "current_phase": organism["current_phase"],
            "hierarchy": {
                "motto": hierarchy["motto"],
                "announced": hierarchy["announced"],
                "chain_tiers": len(hierarchy["chain"]),
            },
            "mission": {
                "title": AXIUM_CHARTER["title"],
                "motto": AXIUM_CHARTER["motto"],
                "broadcast": mission["broadcast"],
                "thread_id": mission["thread_id"],
                "capital_focus": AXIUM_CHARTER.get("capital_focus", ""),
            },
            "organism": {
                "planned_agents": organism["planned_agent_count"],
                "media_division": len(organism["divisions"]["media"]["agents"]),
                "media_active": sum(
                    1 for a in growth if a["agent_id"] in MEDIA_AGENT_IDS_SET
                ),
                "agent_standings": organism["agent_standings"],
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
                "ecosystem_assembly": {
                    "agents": list(ECOSYSTEM_ASSEMBLY_AGENTS),
                    "description": "Mesh proof + medya dalgası + sermaye radarı — tam ekosistem",
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
