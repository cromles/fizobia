"""Ajan DAG — kenarlar şema ile tanımlı; geçersiz bağlantı tanım zamanında imkansız."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Set, Tuple

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

from app.mesh.cellular_taxonomy import CELLULAR_AGENT_IDS, CELLULAR_SET

# Açık DAG kenarları — yalnızca burada tanımlı yönlü bağlantılar geçerlidir
AGENT_DAG_EDGES: Tuple[Tuple[str, str], ...] = (
    (WEB_ID, MACRO_ID),
    (WEB_ID, ORCHESTRATOR_ID),
    (WEB_ID, CRITIC_AGENT_ID),
    (SENTIMENT_ID, MACRO_ID),
    (SENTIMENT_ID, ORCHESTRATOR_ID),
    (SENTIMENT_ID, MARKET_ID),
    (ONCHAIN_ID, MACRO_ID),
    (ONCHAIN_ID, THREAT_ID),
    (ONCHAIN_ID, ORCHESTRATOR_ID),
    (MACRO_ID, ORCHESTRATOR_ID),
    (MACRO_ID, MARKET_ID),
    (MACRO_ID, YIELD_ID),
    (ORCHESTRATOR_ID, MARKET_ID),
    (ORCHESTRATOR_ID, YIELD_ID),
    (ORCHESTRATOR_ID, STORY_ID),
    (ORCHESTRATOR_ID, CRITIC_AGENT_ID),
    (ORCHESTRATOR_ID, THREAT_ID),
    (MARKET_ID, CRITIC_AGENT_ID),
    (MARKET_ID, ORCHESTRATOR_ID),
    (YIELD_ID, CRITIC_AGENT_ID),
    (YIELD_ID, ORCHESTRATOR_ID),
    (STORY_ID, CRITIC_AGENT_ID),
    (STORY_ID, ORCHESTRATOR_ID),
    (CRITIC_AGENT_ID, ORCHESTRATOR_ID),
    (CRITIC_AGENT_ID, MARKET_ID),
    (CRITIC_AGENT_ID, YIELD_ID),
    (CRITIC_AGENT_ID, STORY_ID),
    (THREAT_ID, ORCHESTRATOR_ID),
    (THREAT_ID, ONCHAIN_ID),
    (THREAT_ID, MARKET_ID),
)

_EDGE_SET: FrozenSet[Tuple[str, str]] = frozenset(AGENT_DAG_EDGES)
_OUTBOUND: Dict[str, Tuple[str, ...]] = {}
_INBOUND: Dict[str, Tuple[str, ...]] = {}


@dataclass(frozen=True)
class DagEdge:
    source: str
    target: str

    def to_public(self) -> Dict[str, str]:
        return {"from": self.source, "to": self.target}


def _validate_dag_at_import() -> None:
    unknown: Set[str] = set()
    for src, dst in AGENT_DAG_EDGES:
        if src not in CELLULAR_SET:
            unknown.add(src)
        if dst not in CELLULAR_SET:
            unknown.add(dst)
    if unknown:
        raise ValueError(f"DAG kenarı bilinmeyen ajan içeriyor: {unknown}")
    out: Dict[str, List[str]] = {aid: [] for aid in CELLULAR_AGENT_IDS}
    inn: Dict[str, List[str]] = {aid: [] for aid in CELLULAR_AGENT_IDS}
    for src, dst in AGENT_DAG_EDGES:
        out[src].append(dst)
        inn[dst].append(src)
    global _OUTBOUND, _INBOUND
    _OUTBOUND = {k: tuple(v) for k, v in out.items()}
    _INBOUND = {k: tuple(v) for k, v in inn.items()}


_validate_dag_at_import()


def is_valid_edge(source: str, target: str) -> bool:
    """Kenar DAG şemasında mı — runtime reddi değil, şema kontrolü."""
    return (source, target) in _EDGE_SET


def outbound_neighbors(agent_id: str) -> Tuple[str, ...]:
    return _OUTBOUND.get(agent_id, ())


def inbound_neighbors(agent_id: str) -> Tuple[str, ...]:
    return _INBOUND.get(agent_id, ())


def list_edges() -> List[DagEdge]:
    return [DagEdge(source=s, target=t) for s, t in AGENT_DAG_EDGES]


def edges_public() -> List[Dict[str, str]]:
    return [e.to_public() for e in list_edges()]


def get_dag_status() -> Dict[str, Any]:
    return {
        "topology": "dag",
        "node_count": len(CELLULAR_AGENT_IDS),
        "edge_count": len(AGENT_DAG_EDGES),
        "edges": edges_public(),
        "nodes": list(CELLULAR_AGENT_IDS),
    }
