from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, Tuple

from app.workers.market_pulse import AGENT_ID as MARKET_ID, DISPLAY_NAME as MARKET_NAME
from app.workers.sentiment_radar import AGENT_ID as SENTIMENT_ID, DISPLAY_NAME as SENTIMENT_NAME
from app.workers.web_crawler import AGENT_ID as WEB_ID, DISPLAY_NAME as WEB_NAME

ORCHESTRATOR_ID = "oam.orchestrator.pipeline.local"
ORCHESTRATOR_NAME = "Pipeline Orchestrator"

FOUNDER_AGENT_IDS: FrozenSet[str] = frozenset({WEB_ID, SENTIMENT_ID, MARKET_ID})

FOUNDER_BOOTSTRAP_ORDER: Tuple[str, ...] = (WEB_ID, SENTIMENT_ID, MARKET_ID, ORCHESTRATOR_ID)


@dataclass(frozen=True)
class FounderRole:
    agent_id: str
    display_name: str
    role: str
    mission: str
    boot_order: int


FOUNDER_ROLES: Dict[str, FounderRole] = {
    WEB_ID: FounderRole(
        agent_id=WEB_ID,
        display_name=WEB_NAME,
        role="scout",
        mission="Dış dünyayı okur — veri girişi ve kaynak keşfi",
        boot_order=1,
    ),
    SENTIMENT_ID: FounderRole(
        agent_id=SENTIMENT_ID,
        display_name=SENTIMENT_NAME,
        role="analyst",
        mission="Sinyal üretir — sentiment ve piyasa psikolojisi",
        boot_order=2,
    ),
    MARKET_ID: FounderRole(
        agent_id=MARKET_ID,
        display_name=MARKET_NAME,
        role="analyst",
        mission="Piyasa verisini yorumlar — fiyat ve momentum",
        boot_order=3,
    ),
    ORCHESTRATOR_ID: FounderRole(
        agent_id=ORCHESTRATOR_ID,
        display_name=ORCHESTRATOR_NAME,
        role="coordinator",
        mission="Ağı büyütür — ajan işe alır, görev dağıtır, mesh'i genişletir",
        boot_order=4,
    ),
}


def is_founder(agent_id: str) -> bool:
    return agent_id in FOUNDER_AGENT_IDS or agent_id == ORCHESTRATOR_ID


def founder_tier(agent_id: str) -> str:
    if agent_id in FOUNDER_AGENT_IDS:
        return "founder"
    if agent_id == ORCHESTRATOR_ID:
        return "coordinator"
    return "growth"
