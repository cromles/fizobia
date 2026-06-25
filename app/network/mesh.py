from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.config import settings
from app.network.public_discovery import PublicPeerDiscovery
from app.network.schemas import PeerNetworkRecord, PublicAnnounceRequest, SignalMessage, SignalType
from app.network.signaling import SignalingHub, build_stun_config
from app.network.tunnel import TunnelHub, TUNNEL_PREFIX
from app.network.webrtc import SignalingOrchestrator, WebRTCSessionManager
from app.protocol.schemas import AgentManifest

logger = logging.getLogger(__name__)


class GlobalNetworkMesh:
    """
    OAM küresel ağ koordinatörü — tünel, WebRTC signaling ve endpoint çözümlemesi.
    """

    def __init__(
        self,
        discovery: PublicPeerDiscovery,
        signaling: SignalingHub,
        tunnel: TunnelHub,
        webrtc: WebRTCSessionManager,
        public_base_url: str,
    ) -> None:
        self.discovery = discovery
        self.signaling = signaling
        self.tunnel = tunnel
        self.webrtc = webrtc
        self.orchestrator = SignalingOrchestrator(webrtc)
        self.public_base_url = public_base_url.rstrip("/")

    def register_tunnel_peer(
        self,
        agent_id: str,
        local_endpoint: str,
        manifest: AgentManifest,
        ttl: int = 300,
    ) -> PeerNetworkRecord:
        tunnel_endpoint = self.tunnel.tunnel_endpoint(agent_id, self.public_base_url)
        updated_manifest = manifest.model_copy(update={"endpoint": tunnel_endpoint})
        record = PeerNetworkRecord(
            agent_id=agent_id,
            manifest=updated_manifest,
            local_endpoint=local_endpoint,
            public_endpoint=tunnel_endpoint,
            nat_type="tunnel",
        )
        self.discovery.announce_public(record, ttl=ttl)
        logger.info(
            "Tünel ajanı kayıtlı: %s → %s (local=%s)",
            agent_id,
            tunnel_endpoint,
            local_endpoint,
        )
        return record

    def register_public_peer(self, request: PublicAnnounceRequest) -> PeerNetworkRecord:
        if self.tunnel.is_connected(request.manifest.agent_id):
            return self.register_tunnel_peer(
                request.manifest.agent_id,
                request.local_endpoint,
                request.manifest,
                ttl=request.ttl,
            )
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

    def resolve_route(self, manifest: AgentManifest) -> Dict[str, str]:
        agent_id = manifest.agent_id
        if self.tunnel.is_connected(agent_id):
            return {"mode": "tunnel", "target": agent_id}
        if manifest.endpoint.startswith(TUNNEL_PREFIX):
            return {"mode": "tunnel", "target": agent_id}
        record = self.discovery.get_record(agent_id)
        if record and record.public_endpoint and record.public_endpoint.startswith(TUNNEL_PREFIX):
            return {"mode": "tunnel", "target": agent_id}
        endpoint = manifest.endpoint
        if record:
            endpoint = record.public_endpoint or record.local_endpoint or endpoint
        return {"mode": "http", "target": endpoint}

    async def execute(
        self,
        manifest: AgentManifest,
        capability: str,
        data: Dict[str, Any],
        http_executor: Any,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        route = self.resolve_route(manifest)
        if route["mode"] == "tunnel":
            agent_id = route["target"]
            if not self.tunnel.is_connected(agent_id):
                return {"error": f"tunnel_offline:{agent_id}"}
            return await self.tunnel.execute_remote(agent_id, capability, data, timeout)

        if self.webrtc.available and self.webrtc._data_channels.get(manifest.agent_id):
            result = await self.webrtc.execute_over_datachannel(
                manifest.agent_id, capability, data, timeout
            )
            if "error" not in result:
                return result

        return await http_executor(route["target"], capability, data, timeout)

    def stun_config(self) -> dict:
        config = build_stun_config(
            self.public_base_url,
            extra_stun=settings.extra_stun_servers,
        )
        config["turn_servers"] = settings.turn_servers
        config["tunnel_url"] = f"{self.public_base_url}/network/tunnel"
        config["webrtc_available"] = self.webrtc.available
        config["protocol"] = "OAM-NAT-v2"
        return config

    async def initiate_webrtc_handshake(self, peer_id: str) -> Dict[str, Any]:
        offer = await self.webrtc.create_offer(peer_id)
        if "error" in offer:
            return offer
        message = SignalMessage(
            type=SignalType.OFFER,
            from_peer="gateway",
            to_peer=peer_id,
            payload=offer,
        )
        await self.signaling.relay(message)
        return offer

    async def handle_incoming_signal(self, message: SignalMessage) -> Optional[Dict[str, Any]]:
        return await self.orchestrator.handle_signal(message)
