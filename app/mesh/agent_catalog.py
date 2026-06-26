"""Ajan kataloğu — isimler, gelir çekirdeği, API kaynakları."""

from __future__ import annotations

from typing import Dict, FrozenSet, Tuple

from app.mesh.critic import CRITIC_AGENT_ID
from app.mesh.proof_pipeline import MESH_PROOF_AGENTS
from app.workers.btc_network import AGENT_ID as BTCNET_ID, DISPLAY_NAME as BTCNET_NAME
from app.workers.defi_pulse import AGENT_ID as DEFI_ID, DISPLAY_NAME as DEFI_NAME
from app.workers.fx_pulse import AGENT_ID as FX_ID, DISPLAY_NAME as FX_NAME
from app.workers.market_pulse import AGENT_ID as MARKET_ID, DISPLAY_NAME as MARKET_NAME
from app.workers.media_brand import AGENT_ID as BRAND_ID, DISPLAY_NAME as BRAND_NAME
from app.workers.media_render import AGENT_ID as RENDER_ID, DISPLAY_NAME as RENDER_NAME
from app.workers.media_story import AGENT_ID as STORY_ID, DISPLAY_NAME as STORY_NAME
from app.workers.on_chain_watcher import AGENT_ID as ONCHAIN_ID, DISPLAY_NAME as ONCHAIN_NAME
from app.workers.sentiment_radar import AGENT_ID as SENTIMENT_ID, DISPLAY_NAME as SENTIMENT_NAME
from app.workers.text_competitors import AGENT_HOOK_ID, AGENT_DATA_ID, AGENT_STORY_ID
from app.workers.web_crawler import AGENT_ID as WEB_ID, DISPLAY_NAME as WEB_NAME

# Pasif ortaklık — gerçek dış veri / x402 geliri üreten çekirdek
REVENUE_CORE_AGENT_IDS: Tuple[str, ...] = (
    MARKET_ID,
    SENTIMENT_ID,
    WEB_ID,
    ONCHAIN_ID,
    FX_ID,
    DEFI_ID,
    BTCNET_ID,
)

REVENUE_CORE_SET: FrozenSet[str] = frozenset(REVENUE_CORE_AGENT_IDS)

AGENT_LABELS: Dict[str, str] = {
    WEB_ID: WEB_NAME,
    SENTIMENT_ID: SENTIMENT_NAME,
    MARKET_ID: MARKET_NAME,
    ONCHAIN_ID: ONCHAIN_NAME,
    FX_ID: FX_NAME,
    DEFI_ID: DEFI_NAME,
    BTCNET_ID: BTCNET_NAME,
    STORY_ID: STORY_NAME,
    BRAND_ID: BRAND_NAME,
    CRITIC_AGENT_ID: "Immune-Critic",
    RENDER_ID: "Reels-Renderer",
    AGENT_HOOK_ID: "Hook-Master",
    AGENT_STORY_ID: "Story-Forge",
    AGENT_DATA_ID: "Data-Pulse",
}

AGENT_API_TAG: Dict[str, str] = {
    MARKET_ID: "CoinGecko · x402",
    SENTIMENT_ID: "Fear&Greed · x402",
    WEB_ID: "Canlı web tarama",
    ONCHAIN_ID: "Base Sepolia RPC",
    FX_ID: "Frankfurter ECB",
    DEFI_ID: "DefiLlama TVL",
    BTCNET_ID: "mempool.space",
}

AGENT_MISSION: Dict[str, str] = {
    MARKET_ID: "Gerçek piyasa fiyatı ve momentum — görev geliri x402 ile havuza akar.",
    SENTIMENT_ID: "Haber ve Fear&Greed sentiment — ödeme sonrası canlı skor.",
    WEB_ID: "Mesh kanıtının 1. halkası — gerçek URL'den veri çeker.",
    ONCHAIN_ID: "Zincir durumu ve ödeme doğrulama — mesh kanıtı 4. adım.",
    FX_ID: "USD/TRY ve döviz — ücretsiz ECB verisi, 7/24.",
    DEFI_ID: "DeFi zincir TVL liderliği — DefiLlama.",
    BTCNET_ID: "BTC blok, mempool ücreti ve spot fiyat.",
}

MESH_PROOF_SET: FrozenSet[str] = frozenset(MESH_PROOF_AGENTS)


def agent_label(agent_id: str) -> str:
    if agent_id in AGENT_LABELS:
        return AGENT_LABELS[agent_id]
    parts = agent_id.replace(".local", "").split(".")
    if len(parts) >= 2:
        return parts[-1].replace("-", " ").title()
    return agent_id


def is_revenue_core(agent_id: str) -> bool:
    return agent_id in REVENUE_CORE_SET


def is_mesh_proof_agent(agent_id: str) -> bool:
    return agent_id in MESH_PROOF_SET
