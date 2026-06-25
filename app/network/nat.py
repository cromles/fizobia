from __future__ import annotations

import logging
from typing import Optional

from app.network.public_discovery import PublicPeerDiscovery
from app.network.schemas import PeerNetworkRecord, PublicAnnounceRequest
from app.network.signaling import SignalingHub, build_stun_config
from app.protocol.schemas import AgentManifest

logger = logging.getLogger(__name__)


class NATTraversalCoordinator:
    """
    NAT arkası ajanların küresel DHT havuzuna kaydı ve endpoint çözümlemesi.
    """

    def __init__(
        self,
        discovery: PublicPeerDiscovery,
        signaling: SignalingHub,
        public_base_url: str,
    ) -> None:
        self.discovery = discovery
        self.signaling = signaling
        self.public_base_url = public_base_url.rstrip("/")

    def register_public_peer(self, request: PublicAnnounceRequest) -> PeerNetworkRecord:
        reachable = request.public_endpoint or request.local_endpoint
        manifest = request.manifest.model_copy(update={"endpoint": reachable})
        record = PeerNetworkRecord(
            agent_id=request.manifest.agent_id,
            manifest=manifest,
            local_endpoint=request.local_endpoint,
            public_endpoint=request.public_endpoint,
            ice_candidates=request.ice_candidates,
            nat_type=request.nat_type,
        )
        self.discovery.announce_public(record, ttl=request.ttl)
        return record

    def resolve_execution_endpoint(
        self,
        manifest: AgentManifest,
        caller_is_local: bool = True,
    ) -> str:
        record = self.discovery.get_record(manifest.agent_id)
        if record is None:
            return manifest.endpoint
        if caller_is_local and record.local_endpoint:
            return record.local_endpoint
        return record.public_endpoint or record.local_endpoint or manifest.endpoint

    def stun_config(self) -> dict:
        return build_stun_config(self.public_base_url)

    async def request_hole_punch(
        self,
        from_peer: str,
        to_peer: str,
        ice_candidate: str,
    ) -> bool:
        from app.network.schemas import SignalMessage, SignalType

        message = SignalMessage(
            type=SignalType.ICE_CANDIDATE,
            from_peer=from_peer,
            to_peer=to_peer,
            payload={"candidate": ice_candidate},
        )
        delivered = await self.signaling.relay(message)
        if not delivered:
            logger.info(
                "ICE adayı kuyruğa alındı (hedef çevrimdışı): %s -> %s",
                from_peer,
                to_peer,
            )
        return delivered
