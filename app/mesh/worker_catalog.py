"""10 hücresel ajan kataloğu — DAG sinaps ağı."""

from __future__ import annotations

from typing import Any, Dict, List

from app.mesh.agent_catalog import AGENT_API_TAG, AGENT_MISSION, agent_label
from app.mesh.agent_dag import edges_public
from app.mesh.cellular_taxonomy import (
    CELLULAR_AGENT_IDS,
    CELLULAR_ORGANISM,
    cell_type_for,
)
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

AGENT_TOKEN_META: Dict[str, Dict[str, Any]] = {
    WEB_ID: {"symbol": "WEB-TKN", "fixed_supply": 1_000_000, "output": "news_feed"},
    SENTIMENT_ID: {"symbol": "SEN-TKN", "fixed_supply": 1_000_000, "output": "sentiment"},
    ONCHAIN_ID: {"symbol": "OCH-TKN", "fixed_supply": 1_000_000, "output": "chain"},
    MACRO_ID: {"symbol": "MAC-TKN", "fixed_supply": 500_000, "output": "macro"},
    ORCHESTRATOR_ID: {"symbol": "CRD-TKN", "fixed_supply": 500_000, "output": "coordinator"},
    MARKET_ID: {"symbol": "MAR-TKN", "fixed_supply": 1_000_000, "output": "market"},
    YIELD_ID: {"symbol": "YLD-TKN", "fixed_supply": 500_000, "output": "yield"},
    STORY_ID: {"symbol": "STY-TKN", "fixed_supply": 500_000, "output": "story"},
    CRITIC_AGENT_ID: {"symbol": "IMM-TKN", "fixed_supply": 500_000, "output": "critic"},
    THREAT_ID: {"symbol": "THR-TKN", "fixed_supply": 500_000, "output": "threat"},
}

WORKER_LIVE_ROUTES: Dict[str, str] = {
    WEB_ID: "/hub/data/web",
    SENTIMENT_ID: "/hub/data/sentiment",
    ONCHAIN_ID: "/hub/data/onchain",
    MACRO_ID: "/hub/data/macro",
    ORCHESTRATOR_ID: "/hub/data/coordinator",
    MARKET_ID: "/hub/data/market",
    YIELD_ID: "/hub/data/yield",
    STORY_ID: "/hub/data/story",
    CRITIC_AGENT_ID: "/hub/data/critic",
    THREAT_ID: "/hub/data/threat",
}

_CELL_MISSION: Dict[str, str] = {c.agent_id: c.mission for c in CELLULAR_ORGANISM}


def build_workers_catalog() -> Dict[str, Any]:
    workers: List[Dict[str, Any]] = []
    for agent_id in CELLULAR_AGENT_IDS:
        token = AGENT_TOKEN_META.get(agent_id, {})
        workers.append(
            {
                "agent_id": agent_id,
                "display_name": agent_label(agent_id),
                "mission": _CELL_MISSION.get(agent_id) or AGENT_MISSION.get(agent_id, ""),
                "api_tag": AGENT_API_TAG.get(agent_id, "mesh"),
                "token_symbol": token.get("symbol", "TKN"),
                "fixed_supply": token.get("fixed_supply", 500_000),
                "output_type": token.get("output", "generic"),
                "live_route": WORKER_LIVE_ROUTES.get(agent_id, ""),
                "cell_type": cell_type_for(agent_id),
                "real_data": True,
            }
        )
    return {
        "count": len(workers),
        "workers": workers,
        "default_agent_id": WEB_ID,
        "mesh_edges": edges_public(),
        "topology": "dag",
        "tagline": "10 hücre · DAG sinaps · gerçek API",
    }
