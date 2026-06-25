from __future__ import annotations

import logging
from typing import Any, Dict, List, Set

from fastapi import WebSocket, WebSocketDisconnect

from app.network.schemas import SignalMessage, SignalType

logger = logging.getLogger(__name__)

DEFAULT_STUN_SERVERS = [
    "stun:stun.l.google.com:19302",
    "stun:stun1.l.google.com:19302",
]


class SignalingHub:
    """
    WebRTC/libp2p öncesi ICE aday değişimi için merkezi signaling.
    Üretimde libp2p relay ile değiştirilebilir.
    """

    def __init__(self) -> None:
        self._connections: Dict[str, WebSocket] = {}
        self._inbox: Dict[str, List[SignalMessage]] = {}

    @property
    def connected_peers(self) -> Set[str]:
        return set(self._connections.keys())

    async def connect(self, peer_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        old = self._connections.get(peer_id)
        if old is not None:
            try:
                await old.close()
            except Exception:
                pass
        self._connections[peer_id] = websocket
        self._inbox.setdefault(peer_id, [])
        logger.info("Signaling bağlantısı: %s", peer_id)

    async def disconnect(self, peer_id: str) -> None:
        self._connections.pop(peer_id, None)

    async def relay(self, message: SignalMessage) -> bool:
        target = self._connections.get(message.to_peer)
        if target is None:
            self._inbox.setdefault(message.to_peer, []).append(message)
            logger.debug("Signaling kuyruk: %s -> %s", message.from_peer, message.to_peer)
            return False
        await target.send_json(message.model_dump())
        return True

    async def listen(self, peer_id: str, websocket: WebSocket) -> None:
        await self.connect(peer_id, websocket)
        try:
            while True:
                raw = await websocket.receive_json()
                message = SignalMessage.model_validate(raw)
                if message.type == SignalType.PING:
                    await websocket.send_json(
                        SignalMessage(
                            type=SignalType.PING,
                            from_peer="hub",
                            to_peer=peer_id,
                            payload={"status": "ok"},
                        ).model_dump()
                    )
                    continue
                await self.relay(message)
        except WebSocketDisconnect:
            await self.disconnect(peer_id)
        except Exception as exc:
            logger.warning("Signaling hatası [%s]: %s", peer_id, exc)
            await self.disconnect(peer_id)

    def drain_inbox(self, peer_id: str) -> List[SignalMessage]:
        messages = self._inbox.pop(peer_id, [])
        return messages


def build_stun_config(signaling_base_url: str, extra_stun: List[str] | None = None) -> Dict[str, Any]:
    return {
        "stun_servers": (extra_stun or []) + DEFAULT_STUN_SERVERS,
        "signaling_url": f"{signaling_base_url.rstrip('/')}/network/signal",
        "turn_servers": [],
        "protocol": "OAM-NAT-v1",
    }
