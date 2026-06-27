"""Gerçek işçi kataloğu — token, canlı veri rotası, kullanım tipi."""

from __future__ import annotations

from typing import Any, Dict, List

from app.mesh.agent_catalog import (
    AGENT_API_TAG,
    AGENT_MISSION,
    EXPERT_AGENT_IDS,
    WORKER_CONSOLE_AGENT_IDS,
    agent_label,
    is_expert_agent,
)
from app.workers.btc_network import AGENT_ID as BTCNET_ID
from app.workers.defi_pulse import AGENT_ID as DEFI_ID
from app.workers.fx_pulse import AGENT_ID as FX_ID
from app.workers.macro_strategist import AGENT_ID as MACRO_ID
from app.workers.market_pulse import AGENT_ID as MARKET_ID
from app.workers.on_chain_watcher import AGENT_ID as ONCHAIN_ID
from app.workers.regulatory_radar import AGENT_ID as REG_ID
from app.workers.sentiment_radar import AGENT_ID as SENTIMENT_ID
from app.workers.threat_intel import AGENT_ID as THREAT_ID
from app.workers.web_crawler import AGENT_ID as WEB_ID
from app.workers.yield_strategist import AGENT_ID as YIELD_ID

# Sabit arz — ilk adım token ekonomisi (spekülasyon değil, işçi payı)
AGENT_TOKEN_META: Dict[str, Dict[str, Any]] = {
    WEB_ID: {"symbol": "WEB-TKN", "fixed_supply": 1_000_000, "output": "news_feed"},
    SENTIMENT_ID: {"symbol": "SEN-TKN", "fixed_supply": 1_000_000, "output": "sentiment"},
    MARKET_ID: {"symbol": "MAR-TKN", "fixed_supply": 1_000_000, "output": "market"},
    ONCHAIN_ID: {"symbol": "OCH-TKN", "fixed_supply": 1_000_000, "output": "chain"},
    FX_ID: {"symbol": "FX-TKN", "fixed_supply": 1_000_000, "output": "fx"},
    DEFI_ID: {"symbol": "DEF-TKN", "fixed_supply": 1_000_000, "output": "defi"},
    BTCNET_ID: {"symbol": "BTC-TKN", "fixed_supply": 1_000_000, "output": "btc_network"},
    MACRO_ID: {"symbol": "MAC-TKN", "fixed_supply": 500_000, "output": "macro"},
    REG_ID: {"symbol": "REG-TKN", "fixed_supply": 500_000, "output": "regulatory"},
    THREAT_ID: {"symbol": "THR-TKN", "fixed_supply": 500_000, "output": "threat"},
    YIELD_ID: {"symbol": "YLD-TKN", "fixed_supply": 500_000, "output": "yield"},
}

WORKER_LIVE_ROUTES: Dict[str, str] = {
    WEB_ID: "/hub/data/web",
    SENTIMENT_ID: "/hub/data/sentiment",
    MARKET_ID: "/hub/data/market",
    ONCHAIN_ID: "/hub/data/onchain",
    FX_ID: "/hub/data/fx",
    DEFI_ID: "/hub/data/defi",
    BTCNET_ID: "/hub/data/btc-network",
    MACRO_ID: "/hub/data/macro",
    REG_ID: "/hub/data/regulatory",
    THREAT_ID: "/hub/data/threat",
    YIELD_ID: "/hub/data/yield",
}


def build_workers_catalog() -> Dict[str, Any]:
    workers: List[Dict[str, Any]] = []
    for agent_id in WORKER_CONSOLE_AGENT_IDS:
        token = AGENT_TOKEN_META.get(agent_id, {})
        workers.append(
            {
                "agent_id": agent_id,
                "display_name": agent_label(agent_id),
                "mission": AGENT_MISSION.get(agent_id, ""),
                "api_tag": AGENT_API_TAG.get(agent_id, ""),
                "token_symbol": token.get("symbol", "TKN"),
                "fixed_supply": token.get("fixed_supply", 1_000_000),
                "output_type": token.get("output", "generic"),
                "live_route": WORKER_LIVE_ROUTES.get(agent_id, ""),
                "real_data": True,
                "tier": "expert" if is_expert_agent(agent_id) else "core",
            }
        )
    return {
        "count": len(workers),
        "core_count": len(WORKER_CONSOLE_AGENT_IDS) - len(EXPERT_AGENT_IDS),
        "expert_count": len(EXPERT_AGENT_IDS),
        "workers": workers,
        "default_agent_id": WEB_ID,
        "tagline": "Gerçek API · gerçek çıktı · her işçinin kendi tokeni",
    }
