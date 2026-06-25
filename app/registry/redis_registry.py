from __future__ import annotations

import logging
from typing import List, Optional

from redis import Redis

from app.protocol.schemas import AgentManifest
from app.registry.agent_registry import RegisteredCapability

logger = logging.getLogger(__name__)


class RedisAgentRegistry:
    """
    Dağıtık OAM ağı için kalıcı ajan kayıt defteri.
    Her manifest JSON olarak Redis'te saklanır; gateway yeniden başlasa bile ağ korunur.
    """

    INDEX_KEY = "oam:agents:index"
    KEY_PREFIX = "oam:agent:"

    def __init__(self, client: Redis, key_prefix: str = KEY_PREFIX) -> None:
        self._client = client
        self._key_prefix = key_prefix
        self.backend_name = "redis"

    def _agent_key(self, agent_id: str) -> str:
        return f"{self._key_prefix}{agent_id}"

    def register(self, manifest: AgentManifest) -> bool:
        key = self._agent_key(manifest.agent_id)
        if self._client.exists(key):
            return False
        pipeline = self._client.pipeline()
        pipeline.set(key, manifest.model_dump_json())
        pipeline.sadd(self.INDEX_KEY, manifest.agent_id)
        pipeline.execute()
        logger.info("Ajan Redis'e kaydedildi: %s", manifest.agent_id)
        return True

    def get(self, agent_id: str) -> Optional[AgentManifest]:
        raw = self._client.get(self._agent_key(agent_id))
        if raw is None:
            return None
        return AgentManifest.model_validate_json(raw)

    def list_manifests(self) -> List[AgentManifest]:
        agent_ids = self._client.smembers(self.INDEX_KEY)
        manifests: List[AgentManifest] = []
        for agent_id in sorted(agent_ids):
            manifest = self.get(agent_id)
            if manifest is not None:
                manifests.append(manifest)
        return manifests

    def list_capabilities(self) -> List[RegisteredCapability]:
        items: List[RegisteredCapability] = []
        for manifest in self.list_manifests():
            for capability in manifest.capabilities:
                items.append(
                    RegisteredCapability(
                        agent_id=manifest.agent_id,
                        endpoint=manifest.endpoint,
                        reliability_score=manifest.reliability_score,
                        cost_per_token=manifest.cost_per_token,
                        capability=capability,
                    )
                )
        return items

    def update_reliability(self, agent_id: str, score: float) -> None:
        manifest = self.get(agent_id)
        if manifest is None:
            return
        manifest.reliability_score = max(0.0, min(1.0, score))
        self._client.set(self._agent_key(agent_id), manifest.model_dump_json())

    def close(self) -> None:
        self._client.close()

    def ping(self) -> bool:
        return bool(self._client.ping())
