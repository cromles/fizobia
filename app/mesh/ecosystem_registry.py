"""Ekosistem kayıt defteri — tüm ajan bölümleri ve birleştirme sırası."""

from __future__ import annotations

from typing import FrozenSet, Tuple

from app.mesh.founders import FOUNDER_STACK_AGENT_IDS
from app.mesh.proof_pipeline import MESH_PROOF_AGENTS
from app.workers.capital_fundraise import AGENT_ID as CAPITAL_ID
from app.workers.media_brand import AGENT_ID as BRAND_ID
from app.workers.media_outreach import AGENT_ID as OUTREACH_ID
from app.workers.media_proof import AGENT_ID as PROOF_MEDIA_ID
from app.workers.media_render import AGENT_ID as RENDER_ID
from app.workers.media_story import AGENT_ID as STORY_ID
from app.mesh.critic import CRITIC_AGENT_ID
from app.workers.text_competitors import ARENA_TEXT_COMPETITORS

MEDIA_AGENT_IDS: Tuple[str, ...] = (STORY_ID, BRAND_ID, OUTREACH_ID, PROOF_MEDIA_ID)
DEPARTMENT_MICRO_AGENT_IDS: Tuple[str, ...] = ARENA_TEXT_COMPETITORS + (CRITIC_AGENT_ID, RENDER_ID)
GROWTH_DIVISION_IDS: Tuple[str, ...] = MEDIA_AGENT_IDS + (CAPITAL_ID,) + DEPARTMENT_MICRO_AGENT_IDS

ECOSYSTEM_STACK_AGENT_IDS: Tuple[str, ...] = FOUNDER_STACK_AGENT_IDS + GROWTH_DIVISION_IDS

# mesh proof → medya zinciri → sermaye radarı
ECOSYSTEM_ASSEMBLY_AGENTS: Tuple[str, ...] = MESH_PROOF_AGENTS + MEDIA_AGENT_IDS + (CAPITAL_ID,)

MEDIA_AGENT_IDS_SET: FrozenSet[str] = frozenset(MEDIA_AGENT_IDS)
ECOSYSTEM_GROWTH_IDS_SET: FrozenSet[str] = frozenset(GROWTH_DIVISION_IDS)


def is_media_agent(agent_id: str) -> bool:
    return agent_id in MEDIA_AGENT_IDS_SET


def is_ecosystem_growth(agent_id: str) -> bool:
    return agent_id in ECOSYSTEM_GROWTH_IDS_SET
