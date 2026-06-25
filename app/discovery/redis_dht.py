from __future__ import annotations

import logging
from typing import List, Optional

from redis import Redis

from app.protocol.schemas import AgentManifest

logger = logging.getLogger(__name__)


class RedisPeerDiscovery:
    """
    Redis tabanlı dağıtık hash tablosu (DHT) benzeri peer discovery.
    Ajanlar heartbeat ile kendilerini duyurur; capability indeksi üzerinden keşfedilir.
    """

    INDEX_KEY = "oam:dht:index"
    PEER_PREFIX = "oam:dht:peer:"
    CAP_PREFIX = "oam:dht:cap:"

    backend_name = "redis"

    def __init__(self, client: Redis) -> None:
        self._client = client

    def _peer_key(self, agent_id: str) -> str:
        return f"{self.PEER_PREFIX}{agent_id}"

    def _cap_key(self, capability_name: str) -> str:
        return f"{self.CAP_PREFIX}{capability_name}"

    def announce(self, manifest: AgentManifest, ttl: int = 60) -> None:
        peer_key = self._peer_key(manifest.agent_id)
        pipeline = self._client.pipeline()
        pipeline.set(peer_key, manifest.model_dump_json(), ex=ttl)
        pipeline.sadd(self.INDEX_KEY, manifest.agent_id)
        for capability in manifest.capabilities:
            pipeline.sadd(self._cap_key(capability.name), manifest.agent_id)
        pipeline.execute()
        logger.debug("DHT announce: %s (ttl=%s)", manifest.agent_id, ttl)

    def _get_alive(self, agent_id: str) -> Optional[AgentManifest]:
        raw = self._client.get(self._peer_key(agent_id))
        if raw is None:
            return None
        return AgentManifest.model_validate_json(raw)

    def find_by_capability(self, capability_name: str) -> List[AgentManifest]:
        agent_ids = self._client.smembers(self._cap_key(capability_name))
        manifests: List[AgentManifest] = []
        for agent_id in agent_ids:
            manifest = self._get_alive(agent_id)
            if manifest is None:
                self._client.srem(self._cap_key(capability_name), agent_id)
                continue
            manifests.append(manifest)
        manifests.sort(key=lambda item: item.reliability_score, reverse=True)
        return manifests

    def list_peers(self) -> List[AgentManifest]:
        agent_ids = self._client.smembers(self.INDEX_KEY)
        manifests: List[AgentManifest] = []
        stale: List[str] = []
        for agent_id in agent_ids:
            manifest = self._get_alive(agent_id)
            if manifest is None:
                stale.append(agent_id)
                continue
            manifests.append(manifest)
        if stale:
            self._client.srem(self.INDEX_KEY, *stale)
        return manifests

    def close(self) -> None:
        self._client.close()

    def ping(self) -> bool:
        return bool(self._client.ping())
