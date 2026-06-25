from __future__ import annotations

import time
from typing import Dict, List, Optional, Protocol

from app.protocol.schemas import AgentManifest


class PeerDiscovery(Protocol):
    backend_name: str

    def announce(self, manifest: AgentManifest, ttl: int = 60) -> None: ...

    def find_by_capability(self, capability_name: str) -> List[AgentManifest]: ...

    def list_peers(self) -> List[AgentManifest]: ...


class InMemoryPeerDiscovery:
    """Tek düğüm geliştirme ortamı için bellek içi DHT."""

    backend_name = "memory"

    def __init__(self) -> None:
        self._peers: Dict[str, tuple[AgentManifest, float]] = {}
        self._capability_index: Dict[str, set[str]] = {}

    def announce(self, manifest: AgentManifest, ttl: int = 60) -> None:
        expires_at = time.time() + ttl
        self._peers[manifest.agent_id] = (manifest, expires_at)
        for capability in manifest.capabilities:
            self._capability_index.setdefault(capability.name, set()).add(manifest.agent_id)

    def _alive_manifest(self, agent_id: str) -> Optional[AgentManifest]:
        entry = self._peers.get(agent_id)
        if entry is None:
            return None
        manifest, expires_at = entry
        if expires_at < time.time():
            self._peers.pop(agent_id, None)
            return None
        return manifest

    def find_by_capability(self, capability_name: str) -> List[AgentManifest]:
        agent_ids = self._capability_index.get(capability_name, set())
        manifests: List[AgentManifest] = []
        for agent_id in list(agent_ids):
            manifest = self._alive_manifest(agent_id)
            if manifest is None:
                agent_ids.discard(agent_id)
                continue
            manifests.append(manifest)
        manifests.sort(key=lambda item: item.reliability_score, reverse=True)
        return manifests

    def list_peers(self) -> List[AgentManifest]:
        manifests: List[AgentManifest] = []
        for agent_id in list(self._peers.keys()):
            manifest = self._alive_manifest(agent_id)
            if manifest is not None:
                manifests.append(manifest)
        return manifests
