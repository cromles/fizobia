from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional

from app.network.schemas import PeerNetworkRecord
from app.protocol.schemas import AgentManifest

logger = logging.getLogger(__name__)


class PublicPeerDiscovery:
    """
    Küresel keşif katmanı — NAT arkasındaki ajanlar public_endpoint ile DHT'ye girer.
    Lokal gateway aynı makinedeki ajanlara local_endpoint üzerinden ulaşır.
    """

    backend_name = "public"

    def __init__(self) -> None:
        self._peers: Dict[str, tuple[PeerNetworkRecord, float]] = {}
        self._capability_index: Dict[str, set[str]] = {}

    def announce_public(
        self,
        record: PeerNetworkRecord,
        ttl: int = 120,
    ) -> None:
        expires_at = time.time() + ttl
        reachable = record.public_endpoint or record.local_endpoint
        manifest = record.manifest.model_copy(update={"endpoint": reachable})
        stored = record.model_copy(update={"manifest": manifest})
        self._peers[record.agent_id] = (stored, expires_at)
        for capability in manifest.capabilities:
            self._capability_index.setdefault(capability.name, set()).add(record.agent_id)
        logger.info(
            "Küresel duyuru: %s local=%s public=%s",
            record.agent_id,
            record.local_endpoint,
            record.public_endpoint,
        )

    def announce(self, manifest: AgentManifest, ttl: int = 60) -> None:
        record = PeerNetworkRecord(
            agent_id=manifest.agent_id,
            manifest=manifest,
            local_endpoint=manifest.endpoint,
            public_endpoint=None,
        )
        self.announce_public(record, ttl=ttl)

    def get_record(self, agent_id: str) -> Optional[PeerNetworkRecord]:
        entry = self._peers.get(agent_id)
        if entry is None:
            return None
        record, expires_at = entry
        if expires_at < time.time():
            self._peers.pop(agent_id, None)
            return None
        return record

    def resolve_endpoint(self, agent_id: str, prefer_local: bool = True) -> Optional[str]:
        record = self.get_record(agent_id)
        if record is None:
            return None
        if prefer_local and record.local_endpoint:
            return record.local_endpoint
        return record.public_endpoint or record.local_endpoint

    def _alive_manifest(self, agent_id: str) -> Optional[AgentManifest]:
        record = self.get_record(agent_id)
        return record.manifest if record else None

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
        return [r.manifest for aid in list(self._peers) if (r := self.get_record(aid))]

    def list_network_records(self) -> List[PeerNetworkRecord]:
        records: List[PeerNetworkRecord] = []
        for agent_id in list(self._peers.keys()):
            record = self.get_record(agent_id)
            if record is not None:
                records.append(record)
        return records
