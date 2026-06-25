"""Gateway başlangıcında örnek ajan manifest'lerini kayıt defterine ve DHT'ye ekler."""

from __future__ import annotations

import logging

from app.agents.builtins import DEFAULT_MANIFESTS
from app.core.router import OpenAgentMeshRouter
from app.discovery.base import PeerDiscovery
from app.investment.factory import get_investment_hub

logger = logging.getLogger(__name__)


def bootstrap_default_agents(
    router: OpenAgentMeshRouter,
    discovery: PeerDiscovery,
) -> int:
    linked = 0
    hub = get_investment_hub()
    for manifest in DEFAULT_MANIFESTS:
        router.upsert_agent(manifest)
        hub.ensure_agent(manifest)
        discovery.announce(manifest, ttl=3600)
        linked += 1
        logger.info("Örnek ajan bağlandı: %s -> %s", manifest.agent_id, manifest.endpoint)
    return linked
