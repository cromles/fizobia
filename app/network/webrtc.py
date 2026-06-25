from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional

from app.network.schemas import SignalMessage, SignalType
from app.network.signaling import DEFAULT_STUN_SERVERS

logger = logging.getLogger(__name__)

try:
    from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription
    from aiortc.contrib.signaling import BYE, candidate_from_sdp, candidate_to_sdp

    AIORTC_AVAILABLE = True
except ImportError:
    AIORTC_AVAILABLE = False
    RTCPeerConnection = None  # type: ignore


class WebRTCSessionManager:
    """
    WebRTC P2P oturum yöneticisi — SDP teklif/yanıt ve ICE aday değişimi.
    aiortc yoksa yalnızca signaling mesajlarını kuyruklar.
    """

    def __init__(self, ice_servers: Optional[List[Dict[str, Any]]] = None) -> None:
        self._ice_servers = ice_servers or self._default_ice_servers()
        self._peers: Dict[str, Any] = {}
        self._data_channels: Dict[str, Any] = {}
        self._pending_execute: Dict[str, asyncio.Future[Dict[str, Any]]] = {}

    @staticmethod
    def _default_ice_servers() -> List[Dict[str, Any]]:
        servers = [{"urls": url} for url in DEFAULT_STUN_SERVERS]
        return servers

    @property
    def available(self) -> bool:
        return AIORTC_AVAILABLE

    async def create_offer(self, peer_id: str) -> Dict[str, Any]:
        if not AIORTC_AVAILABLE:
            return {"error": "aiortc_not_installed", "sdp": None}

        pc = RTCPeerConnection(configuration={"iceServers": self._ice_servers})
        self._peers[peer_id] = pc
        channel = pc.createDataChannel("oam")
        self._data_channels[peer_id] = channel

        @channel.on("message")
        def on_message(message: str | bytes) -> None:
            asyncio.create_task(self._handle_channel_message(peer_id, message))

        @pc.on("icecandidate")
        async def on_icecandidate(candidate: RTCIceCandidate | None) -> None:
            if candidate is not None:
                logger.debug("ICE aday üretildi [%s]", peer_id)

        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        return {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}

    async def accept_answer(self, peer_id: str, sdp: str, sdp_type: str) -> Dict[str, Any]:
        if not AIORTC_AVAILABLE:
            return {"error": "aiortc_not_installed"}
        pc = self._peers.get(peer_id)
        if pc is None:
            return {"error": "peer_not_found"}
        await pc.setRemoteDescription(RTCSessionDescription(sdp=sdp, type=sdp_type))
        return {"status": "connected"}

    async def add_ice_candidate(self, peer_id: str, candidate_sdp: str) -> Dict[str, Any]:
        if not AIORTC_AVAILABLE:
            return {"error": "aiortc_not_installed"}
        pc = self._peers.get(peer_id)
        if pc is None:
            return {"error": "peer_not_found"}
        candidate = candidate_from_sdp(candidate_sdp)
        await pc.addIceCandidate(candidate)
        return {"status": "candidate_added"}

    async def execute_over_datachannel(
        self,
        peer_id: str,
        capability: str,
        data: Dict[str, Any],
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        channel = self._data_channels.get(peer_id)
        if channel is None or channel.readyState != "open":
            return {"error": "webrtc_channel_not_open"}

        request_id = __import__("uuid").uuid4().hex
        loop = asyncio.get_running_loop()
        future: asyncio.Future[Dict[str, Any]] = loop.create_future()
        self._pending_execute[request_id] = future
        payload = json.dumps(
            {
                "type": "execute",
                "request_id": request_id,
                "capability": capability,
                "data": data,
            }
        )
        channel.send(payload)
        try:
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending_execute.pop(request_id, None)
            return {"error": "webrtc_execute_timeout"}

    async def _handle_channel_message(self, peer_id: str, message: str | bytes) -> None:
        try:
            if isinstance(message, bytes):
                message = message.decode()
            payload = json.loads(message)
            if payload.get("type") == "execute_response":
                request_id = payload.get("request_id")
                future = self._pending_execute.pop(request_id, None)
                if future and not future.done():
                    future.set_result(payload.get("result", {}))
        except Exception as exc:
            logger.warning("WebRTC mesaj hatası [%s]: %s", peer_id, exc)

    async def close_peer(self, peer_id: str) -> None:
        pc = self._peers.pop(peer_id, None)
        self._data_channels.pop(peer_id, None)
        if pc is not None:
            await pc.close()


class SignalingOrchestrator:
    """Signaling mesajlarını WebRTC oturum yöneticisine yönlendirir."""

    def __init__(self, webrtc: WebRTCSessionManager) -> None:
        self.webrtc = webrtc

    async def handle_signal(self, message: SignalMessage) -> Optional[Dict[str, Any]]:
        if message.type == SignalType.OFFER:
            return await self.webrtc.create_offer(message.from_peer)
        if message.type == SignalType.ANSWER:
            sdp = message.payload.get("sdp", "")
            sdp_type = message.payload.get("type", "answer")
            return await self.webrtc.accept_answer(message.from_peer, sdp, sdp_type)
        if message.type == SignalType.ICE_CANDIDATE:
            candidate = message.payload.get("candidate", "")
            return await self.webrtc.add_ice_candidate(message.to_peer, candidate)
        return None
