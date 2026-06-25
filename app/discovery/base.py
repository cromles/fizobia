from __future__ import annotations

from typing import List, Protocol

from app.protocol.schemas import AgentManifest


class PeerDiscovery(Protocol):
    backend_name: str

    def announce(self, manifest: AgentManifest, ttl: int = 60) -> None: ...

    def find_by_capability(self, capability_name: str) -> List[AgentManifest]: ...

    def list_peers(self) -> List[AgentManifest]: ...
