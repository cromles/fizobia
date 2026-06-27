"""Hücresel organizma — 10 ajan, 4 uzmanlaşma tipi, mesh sinir topolojisi."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Tuple

from app.mesh.agent_catalog import agent_label
from app.mesh.critic import CRITIC_AGENT_ID
from app.mesh.founders import ORCHESTRATOR_ID
from app.workers.macro_strategist import AGENT_ID as MACRO_ID
from app.workers.market_pulse import AGENT_ID as MARKET_ID
from app.workers.media_story import AGENT_ID as STORY_ID
from app.workers.on_chain_watcher import AGENT_ID as ONCHAIN_ID
from app.workers.sentiment_radar import AGENT_ID as SENTIMENT_ID
from app.workers.threat_intel import AGENT_ID as THREAT_ID
from app.workers.web_crawler import AGENT_ID as WEB_ID
from app.workers.yield_strategist import AGENT_ID as YIELD_ID

CELL_SENSORY = "sensory"
CELL_BRAIN = "brain"
CELL_MUSCLE = "muscle"
CELL_IMMUNE = "immune"

CELL_TYPES: Tuple[str, ...] = (CELL_SENSORY, CELL_BRAIN, CELL_MUSCLE, CELL_IMMUNE)

CELL_LABELS_TR: Dict[str, str] = {
    CELL_SENSORY: "Duyu Hücresi",
    CELL_BRAIN: "Beyin / Karar",
    CELL_MUSCLE: "Kas / Eylem",
    CELL_IMMUNE: "Bağışıklık / Hata",
}


@dataclass(frozen=True)
class CellularAgent:
    agent_id: str
    cell_type: str
    role: str
    mission: str

    def to_public(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "display_name": agent_label(self.agent_id),
            "cell_type": self.cell_type,
            "cell_label": CELL_LABELS_TR.get(self.cell_type, self.cell_type),
            "role": self.role,
            "mission": self.mission,
        }


# 10 ajan — her biri tek iş; hepsine her şeyi yaptırma
CELLULAR_ORGANISM: Tuple[CellularAgent, ...] = (
    CellularAgent(
        WEB_ID,
        CELL_SENSORY,
        "web_scanner",
        "Web ve RSS tarama — dış dünyadan ham sinyal.",
    ),
    CellularAgent(
        SENTIMENT_ID,
        CELL_SENSORY,
        "social_pulse",
        "Sosyal duyarlılık ve haber tonu — erken uyarı.",
    ),
    CellularAgent(
        ONCHAIN_ID,
        CELL_SENSORY,
        "api_stream",
        "Zincir ve API akışları — mempool, blok, ödeme sinyali.",
    ),
    CellularAgent(
        MACRO_ID,
        CELL_BRAIN,
        "macro_strategy",
        "Makro veriyi sentezle — risk tonu ve strateji öner.",
    ),
    CellularAgent(
        ORCHESTRATOR_ID,
        CELL_BRAIN,
        "coordinator",
        "Karar merkezi — hangi kas hücresi ne zaman çalışır.",
    ),
    CellularAgent(
        MARKET_ID,
        CELL_MUSCLE,
        "market_action",
        "Piyasa emri ve fiyat aksiyonu — işi bitir.",
    ),
    CellularAgent(
        YIELD_ID,
        CELL_MUSCLE,
        "yield_action",
        "DeFi yield ve sermaye yerleşimi — eylem.",
    ),
    CellularAgent(
        STORY_ID,
        CELL_MUSCLE,
        "content_action",
        "İçerik üret ve yayınla — metin, hikaye, çıktı.",
    ),
    CellularAgent(
        CRITIC_AGENT_ID,
        CELL_IMMUNE,
        "quality_gate",
        "Çıktı denetimi — hatalı kas hücresini durdur.",
    ),
    CellularAgent(
        THREAT_ID,
        CELL_IMMUNE,
        "security_gate",
        "Tehdit ve CVE radarı — güvenlik kilidi.",
    ),
)

CELLULAR_AGENT_IDS: Tuple[str, ...] = tuple(c.agent_id for c in CELLULAR_ORGANISM)
CELLULAR_SET: FrozenSet[str] = frozenset(CELLULAR_AGENT_IDS)

_AGENT_INDEX: Dict[str, CellularAgent] = {c.agent_id: c for c in CELLULAR_ORGANISM}

# Mesh (ağ) — doğrusal fabrika bandı değil; duyu→beyin paralel, bağışıklık kası durdurabilir
MESH_ADJACENCY: Dict[str, Tuple[str, ...]] = {
    WEB_ID: (MACRO_ID, ORCHESTRATOR_ID, CRITIC_AGENT_ID),
    SENTIMENT_ID: (MACRO_ID, ORCHESTRATOR_ID, MARKET_ID),
    ONCHAIN_ID: (MACRO_ID, THREAT_ID, ORCHESTRATOR_ID),
    MACRO_ID: (ORCHESTRATOR_ID, MARKET_ID, YIELD_ID),
    ORCHESTRATOR_ID: (MARKET_ID, YIELD_ID, STORY_ID, CRITIC_AGENT_ID, THREAT_ID),
    MARKET_ID: (CRITIC_AGENT_ID, ORCHESTRATOR_ID),
    YIELD_ID: (CRITIC_AGENT_ID, ORCHESTRATOR_ID),
    STORY_ID: (CRITIC_AGENT_ID, ORCHESTRATOR_ID),
    CRITIC_AGENT_ID: (ORCHESTRATOR_ID, MARKET_ID, YIELD_ID, STORY_ID),
    THREAT_ID: (ORCHESTRATOR_ID, ONCHAIN_ID, MARKET_ID),
}

MUSCLE_AGENT_IDS: Tuple[str, ...] = tuple(
    c.agent_id for c in CELLULAR_ORGANISM if c.cell_type == CELL_MUSCLE
)
SENSORY_AGENT_IDS: Tuple[str, ...] = tuple(
    c.agent_id for c in CELLULAR_ORGANISM if c.cell_type == CELL_SENSORY
)
BRAIN_AGENT_IDS: Tuple[str, ...] = tuple(
    c.agent_id for c in CELLULAR_ORGANISM if c.cell_type == CELL_BRAIN
)
IMMUNE_AGENT_IDS: Tuple[str, ...] = tuple(
    c.agent_id for c in CELLULAR_ORGANISM if c.cell_type == CELL_IMMUNE
)

# Pipeline → hangi hücre tipleri aktif
PIPELINE_CELL_USAGE: Dict[str, Tuple[str, ...]] = {
    "mesh_proof": (CELL_SENSORY, CELL_BRAIN, CELL_MUSCLE, CELL_IMMUNE),
    "ecosystem_assembly": (CELL_SENSORY, CELL_BRAIN, CELL_MUSCLE, CELL_IMMUNE),
    "arena": (CELL_BRAIN, CELL_MUSCLE, CELL_IMMUNE),
    "article": (CELL_SENSORY, CELL_MUSCLE, CELL_IMMUNE),
    "goal": (CELL_BRAIN, CELL_MUSCLE),
}


def cell_type_for(agent_id: str) -> str:
    spec = _AGENT_INDEX.get(agent_id)
    return spec.cell_type if spec else CELL_MUSCLE


def is_mesh_neighbor(from_agent: str, to_agent: str) -> bool:
    """Ağ topolojisinde doğrudan sinaps var mı."""
    if from_agent == to_agent:
        return True
    neighbors = MESH_ADJACENCY.get(from_agent, ())
    if to_agent in neighbors:
        return True
    return from_agent in MESH_ADJACENCY.get(to_agent, ())


def agents_by_cell(cell_type: str) -> List[Dict[str, Any]]:
    return [c.to_public() for c in CELLULAR_ORGANISM if c.cell_type == cell_type]


def get_cellular_taxonomy() -> Dict[str, Any]:
    by_type = {ct: agents_by_cell(ct) for ct in CELL_TYPES}
    return {
        "philosophy": "10 ajan — uzmanlaşma şart. Doğrusal fabrika bandı yok; mesh sinir ağı.",
        "total_agents": len(CELLULAR_ORGANISM),
        "cell_types": [
            {
                "code": ct,
                "label": CELL_LABELS_TR[ct],
                "count": len(by_type[ct]),
                "agents": by_type[ct],
            }
            for ct in CELL_TYPES
        ],
        "agents": [c.to_public() for c in CELLULAR_ORGANISM],
        "mesh_topology": "network",
        "mesh_adjacency": {
            aid: list(neighbors) for aid, neighbors in MESH_ADJACENCY.items()
        },
        "muscle_agents": list(MUSCLE_AGENT_IDS),
        "sensory_agents": list(SENSORY_AGENT_IDS),
        "brain_agents": list(BRAIN_AGENT_IDS),
        "immune_agents": list(IMMUNE_AGENT_IDS),
    }
