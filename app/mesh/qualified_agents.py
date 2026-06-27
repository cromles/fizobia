"""Hub yatırım yüzeyi — yalnızca gelir üreten çekirdek ajanlar."""

from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

from app.mesh.agent_catalog import REVENUE_CORE_AGENT_IDS, REVENUE_CORE_SET, is_revenue_core

# Geriye dönük importlar
HUB_QUALIFIED_AGENT_IDS: Tuple[str, ...] = REVENUE_CORE_AGENT_IDS
HUB_QUALIFIED_SET = REVENUE_CORE_SET


def is_hub_qualified(agent_id: str) -> bool:
    return is_revenue_core(agent_id)


def filter_hub_qualified(agent_ids: Iterable[str]) -> Tuple[str, ...]:
    return tuple(aid for aid in agent_ids if is_hub_qualified(aid))


def filter_manifests(manifests: Sequence, *, include_hidden: bool = False) -> List:
    if include_hidden:
        return list(manifests)
    return [m for m in manifests if is_hub_qualified(m.agent_id)]
