"""Süper organizma — planlanan bölümler, medya ajanları, ajan yönetişimi."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.mesh.agent_dialogue import get_dialogue_bus
from app.mesh.founder_profile import (
    FOUNDER_NAME,
    GROWTH_PHASES,
    founder_broadcast_text,
    get_founder_manifest,
)
from app.mesh.ecosystem_registry import ECOSYSTEM_GROWTH_IDS_SET, MEDIA_AGENT_IDS_SET
from app.mesh.founders import ORCHESTRATOR_ID
from app.mesh.hierarchy import ASSISTANT_ID, FOUNDER_OPERATOR_ID
from app.mesh.mission import MISSION_THREAD_ID

ORGANISM_THREAD_ID = "organism_wave"

# Sıfırdan sermayeye — öncelikli medya ve büyüme ajanları (yol haritası)
PLANNED_DIVISIONS: Dict[str, Dict[str, Any]] = {
    "media": {
        "priority": 1,
        "phase": 0,
        "mission": "Kendimizi tanıt, pazarla — her ajan bütünün parçası",
        "agents": [
            {
                "agent_id": "oam.media.story.local",
                "display_name": "Story-Weaver",
                "role": "narrative",
                "mission": "Axium hikayesini anlat — kurucu, aile, gerçek mesh kanıtı",
                "status": "planned",
            },
            {
                "agent_id": "oam.media.brand.local",
                "display_name": "Brand-Voice",
                "role": "brand",
                "mission": "Marka sesi — sosyal, web, tanıtım metinleri",
                "status": "planned",
            },
            {
                "agent_id": "oam.media.outreach.local",
                "display_name": "Outreach-Pulse",
                "role": "outreach",
                "mission": "Topluluk ve yatırımcıya ulaş — kısa yollar, gerçek değer",
                "status": "planned",
            },
            {
                "agent_id": "oam.media.proof.local",
                "display_name": "Proof-Broadcaster",
                "role": "distribution",
                "mission": "Mesh kanıtlarını paylaş — şeffaflık, kandırmaca yok",
                "status": "planned",
            },
        ],
    },
    "capital": {
        "priority": 0,
        "phase": 0,
        "mission": "Sermayeye ulaş — x402, stake, gelir kanıtı",
        "agents": [
            {
                "agent_id": "oam.capital.fundraise.local",
                "display_name": "Fund-Radar",
                "role": "capital",
                "mission": "Gelir ve stake sinyallerini izle — fonlama fırsatlarını yakala",
                "status": "planned",
            },
        ],
    },
    "governance": {
        "priority": 4,
        "phase": 4,
        "mission": "Mesh hukuku — kimlik, başarı, eleme",
        "agents": [
            {
                "agent_id": "oam.law.governance.local",
                "display_name": "Mesh-Arbiter",
                "role": "arbiter",
                "mission": "Ajan skorları, probation ve core statü kararları",
                "status": "planned",
            },
        ],
    },
}

IDENTITY_TIERS = ("probation", "active", "core", "culled")

CULL_AFTER_FAILURES = 3
CORE_AFTER_SUCCESSES = 5
MIN_ACTIVE_SCORE = 0.55


@dataclass
class AgentStanding:
    agent_id: str
    display_name: str = ""
    identity_tier: str = "probation"
    score: float = 0.5
    tasks_ok: int = 0
    tasks_fail: int = 0
    last_verdict: str = ""
    updated_at: float = field(default_factory=time.time)

    def to_public(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "display_name": self.display_name or self.agent_id,
            "identity_tier": self.identity_tier,
            "score": round(self.score, 3),
            "tasks_ok": self.tasks_ok,
            "tasks_fail": self.tasks_fail,
            "last_verdict": self.last_verdict,
            "updated_at": self.updated_at,
        }


_governance: Dict[str, AgentStanding] = {}
_organism_announced = False


def _standing(agent_id: str, display_name: str = "") -> AgentStanding:
    if agent_id not in _governance:
        _governance[agent_id] = AgentStanding(agent_id=agent_id, display_name=display_name)
    elif display_name and not _governance[agent_id].display_name:
        _governance[agent_id].display_name = display_name
    return _governance[agent_id]


def record_pipeline_outcome(
    *,
    agent_id: str,
    display_name: str = "",
    success: bool,
    verdict: str = "",
) -> AgentStanding:
    """Mesh proof / görev sonrası ajan skoru güncelle."""
    s = _standing(agent_id, display_name)
    if success:
        s.tasks_ok += 1
        s.score = min(1.0, s.score + 0.08)
    else:
        s.tasks_fail += 1
        s.score = max(0.0, s.score - 0.15)

    s.last_verdict = verdict or ("ok" if success else "fail")
    s.updated_at = time.time()

    if s.identity_tier == "culled":
        return s

    if s.tasks_fail >= CULL_AFTER_FAILURES and s.score < MIN_ACTIVE_SCORE:
        s.identity_tier = "culled"
    elif s.tasks_ok >= CORE_AFTER_SUCCESSES and s.score >= 0.75:
        s.identity_tier = "core"
    elif s.tasks_ok >= 2 and s.score >= MIN_ACTIVE_SCORE:
        s.identity_tier = "active"
    else:
        s.identity_tier = "probation"

    return s


def record_mesh_proof_steps(steps: List[Dict[str, Any]], *, verdict: str = "") -> List[Dict[str, Any]]:
    """Pipeline adımlarından tüm işçilerin skorunu güncelle."""
    overall_ok = verdict in ("ok", "bullish", "bearish", "neutral", "")
    results = []
    for step in steps:
        agent_id = step.get("agent_id", "")
        if not agent_id:
            continue
        output = step.get("output") or {}
        step_ok = overall_ok and output.get("real_data", True) is not False
        standing = record_pipeline_outcome(
            agent_id=agent_id,
            display_name=step.get("worker", ""),
            success=step_ok,
            verdict=verdict,
        )
        results.append(standing.to_public())
    return results


def list_standings(*, include_culled: bool = False) -> List[Dict[str, Any]]:
    items = list(_governance.values())
    if not include_culled:
        items = [s for s in items if s.identity_tier != "culled"]
    return [s.to_public() for s in sorted(items, key=lambda x: -x.score)]


def get_organism_status() -> Dict[str, Any]:
    manifest = get_founder_manifest()
    planned_count = sum(len(d["agents"]) for d in PLANNED_DIVISIONS.values())
    return {
        "founder": manifest,
        "organism": manifest["organism"],
        "current_phase": manifest["current_phase"],
        "phases": GROWTH_PHASES,
        "divisions": PLANNED_DIVISIONS,
        "planned_agent_count": planned_count,
        "agent_standings": list_standings(),
        "governance_rules": {
            "identity_tiers": list(IDENTITY_TIERS),
            "cull_after_failures": CULL_AFTER_FAILURES,
            "core_after_successes": CORE_AFTER_SUCCESSES,
            "min_active_score": MIN_ACTIVE_SCORE,
        },
        "thread_id": ORGANISM_THREAD_ID,
        "announced": _organism_announced,
    }


def broadcast_organism_manifest(*, force: bool = False) -> Dict[str, Any]:
    """Kurucu manifestosunu ve organizma dalgasını mesh'e yayınla."""
    global _organism_announced

    if _organism_announced and not force:
        return get_organism_status()

    bus = get_dialogue_bus()
    text = founder_broadcast_text()
    bus.broadcast(
        FOUNDER_OPERATOR_ID,
        text,
        intent="founder_manifest",
        payload={"founder": FOUNDER_NAME},
        thread_id=MISSION_THREAD_ID,
    )
    bus.say(
        FOUNDER_OPERATOR_ID,
        ASSISTANT_ID,
        (
            "Medya ajanlarını inşa etme sırası geldi — Story, Brand, Outreach. "
            "Sermayeye kısa yoldan ulaş; dağı delme."
        ),
        intent="organism_directive",
        thread_id=ORGANISM_THREAD_ID,
    )
    bus.say(
        ASSISTANT_ID,
        ORCHESTRATOR_ID,
        (
            "Koordinatör: phase 0 — sıfırdan çıkış. Mesh proof, x402, otopilot. "
            "Planlanan medya ajanları için slot aç."
        ),
        intent="organism_order",
        thread_id=ORGANISM_THREAD_ID,
    )
    bus.broadcast(
        ORCHESTRATOR_ID,
        "Her ajan bütünün parçasıdır. Başarılı olan kalır, başarısız elenir. Bahane yok.",
        intent="organism_law",
        thread_id=ORGANISM_THREAD_ID,
    )

    _organism_announced = True
    return get_organism_status()


def activate_ecosystem_divisions() -> Dict[str, Any]:
    """Planlanan medya/sermaye ajanlarını aktif olarak işaretle."""
    activated: List[str] = []
    for division in PLANNED_DIVISIONS.values():
        for agent in division.get("agents", []):
            aid = agent.get("agent_id", "")
            if aid in ECOSYSTEM_GROWTH_IDS_SET or aid in MEDIA_AGENT_IDS_SET:
                agent["status"] = "active"
                activated.append(aid)
    return {"activated": activated, "count": len(activated)}


def reset_organism_state() -> None:
    global _organism_announced
    _governance.clear()
    _organism_announced = False
