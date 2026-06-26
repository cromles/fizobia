"""Hub yatırım yüzeyi — yalnızca kalifiye (gerçek iş yapan) ajanlar."""

from __future__ import annotations

from typing import FrozenSet, Iterable, List, Sequence, Tuple

from app.mesh.critic import CRITIC_AGENT_ID
from app.mesh.founders import ORCHESTRATOR_ID
from app.workers.btc_network import AGENT_ID as BTCNET_ID
from app.workers.capital_fundraise import AGENT_ID as CAPITAL_ID
from app.workers.defi_pulse import AGENT_ID as DEFI_ID
from app.workers.fx_pulse import AGENT_ID as FX_ID
from app.workers.market_pulse import AGENT_ID as MARKET_PULSE_ID
from app.workers.media_brand import AGENT_ID as BRAND_ID
from app.workers.media_outreach import AGENT_ID as OUTREACH_ID
from app.workers.media_proof import AGENT_ID as PROOF_MEDIA_ID
from app.workers.media_render import AGENT_ID as RENDER_ID
from app.workers.media_story import AGENT_ID as STORY_ID
from app.workers.on_chain_watcher import AGENT_ID as ON_CHAIN_ID
from app.workers.sentiment_radar import AGENT_ID as SENTIMENT_RADAR_ID
from app.workers.text_competitors import (
    AGENT_DATA_ID,
    AGENT_HOOK_ID,
    AGENT_STORY_ID,
)
from app.workers.web_crawler import AGENT_ID as WEB_CRAWLER_ID

# Hub'da gösterilen — veri, içerik, arena temsilcisi
HUB_QUALIFIED_AGENT_IDS: Tuple[str, ...] = (
    WEB_CRAWLER_ID,
    SENTIMENT_RADAR_ID,
    MARKET_PULSE_ID,
    ON_CHAIN_ID,
    FX_ID,
    DEFI_ID,
    BTCNET_ID,
    STORY_ID,
    BRAND_ID,
    CRITIC_AGENT_ID,
    RENDER_ID,
    AGENT_HOOK_ID,
)

HUB_QUALIFIED_SET: FrozenSet[str] = frozenset(HUB_QUALIFIED_AGENT_IDS)

# Hub'da gösterilmez; arena/altyapı için arka planda çalışır
HUB_BACKGROUND_AGENT_IDS: FrozenSet[str] = frozenset(
    {
        ORCHESTRATOR_ID,
        AGENT_STORY_ID,
        AGENT_DATA_ID,
        OUTREACH_ID,
        PROOF_MEDIA_ID,
        CAPITAL_ID,
    }
)


def is_hub_qualified(agent_id: str) -> bool:
    return agent_id in HUB_QUALIFIED_SET


def filter_hub_qualified(agent_ids: Iterable[str]) -> Tuple[str, ...]:
    return tuple(aid for aid in agent_ids if is_hub_qualified(aid))


def filter_manifests(manifests: Sequence, *, include_hidden: bool = False) -> List:
    if include_hidden:
        return list(manifests)
    return [m for m in manifests if is_hub_qualified(m.agent_id)]
