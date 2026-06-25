from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Protocol

from app.protocol.schemas import AgentCapability, AgentManifest


@dataclass(frozen=True)
class RegisteredCapability:
    agent_id: str
    endpoint: str
    reliability_score: float
    cost_per_token: float
    capability: AgentCapability


class AgentRegistry(Protocol):
    def register(self, manifest: AgentManifest) -> bool: ...

    def upsert(self, manifest: AgentManifest) -> None: ...

    def get(self, agent_id: str) -> Optional[AgentManifest]: ...

    def list_manifests(self) -> List[AgentManifest]: ...

    def list_capabilities(self) -> List[RegisteredCapability]: ...

    def update_reliability(self, agent_id: str, score: float) -> None: ...


class InMemoryAgentRegistry:
    """Geliştirme ve tek düğümlü gateway için bellek içi registry."""

    backend_name = "memory"

    def __init__(self) -> None:
        self._manifests: Dict[str, AgentManifest] = {}

    def register(self, manifest: AgentManifest) -> bool:
        if manifest.agent_id in self._manifests:
            return False
        self._manifests[manifest.agent_id] = manifest
        return True

    def upsert(self, manifest: AgentManifest) -> None:
        self._manifests[manifest.agent_id] = manifest

    def get(self, agent_id: str) -> Optional[AgentManifest]:
        return self._manifests.get(agent_id)

    def list_manifests(self) -> List[AgentManifest]:
        return list(self._manifests.values())

    def list_capabilities(self) -> List[RegisteredCapability]:
        items: List[RegisteredCapability] = []
        for manifest in self._manifests.values():
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
        manifest = self._manifests.get(agent_id)
        if manifest is None:
            return
        manifest.reliability_score = max(0.0, min(1.0, score))

    def __iter__(self) -> Iterator[AgentManifest]:
        return iter(self._manifests.values())
