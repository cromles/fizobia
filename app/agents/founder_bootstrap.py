"""Kurucu ajan mesh'i — 3 işçi + 1 koordinatör ile başlat."""

from __future__ import annotations

import logging

from app.agents.extended_builtins import EXTENDED_MANIFESTS
from app.core.router import OpenAgentMeshRouter
from app.discovery.base import PeerDiscovery
from app.mesh.founders import (
    FOUNDER_BOOTSTRAP_ORDER,
    GROWTH_SEED_AGENT_IDS,
    ORCHESTRATOR_ID,
)
from app.mesh.growth_protocol import get_growth_protocol, init_growth_protocol

logger = logging.getLogger(__name__)

_FOUNDER_IDS = frozenset(FOUNDER_BOOTSTRAP_ORDER)


def _founder_manifests():
    return [m for m in EXTENDED_MANIFESTS if m.agent_id in _FOUNDER_IDS]


def bootstrap_founder_agents(router: OpenAgentMeshRouter, discovery: PeerDiscovery) -> int:
    """Sadece kurucu dörtlüyü kayıt defterine ve DHT'ye ekler."""
    from app.investment.factory import get_investment_hub

    hub = get_investment_hub()
    linked = 0
    for manifest in _founder_manifests():
        router.upsert_agent(manifest)
        hub.ensure_agent(manifest)
        discovery.announce(manifest, ttl=3600)
        linked += 1
        logger.info("Kurucu ajan: %s -> %s", manifest.agent_id, manifest.endpoint)

    growth = init_growth_protocol(router, discovery)
    growth.bootstrap_founders()
    # Büyüme tohumu — On-Chain-Watcher mesh'e katılır
    for manifest in EXTENDED_MANIFESTS:
        if manifest.agent_id in GROWTH_SEED_AGENT_IDS:
            growth.join_agent(manifest)
    return linked


def bootstrap_full_agents(router: OpenAgentMeshRouter, discovery: PeerDiscovery) -> int:
    """Tam yığın — kurucular + legacy mock ajanlar."""
    from app.agents.bootstrap import bootstrap_default_agents

    count = bootstrap_default_agents(router, discovery)
    growth = init_growth_protocol(router, discovery)
    growth.bootstrap_founders()
    return count
