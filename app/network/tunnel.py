from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

TUNNEL_PREFIX = "oam+tunnel://"
EXECUTE_TIMEOUT = 30.0


class TunnelHub:
    """
    NAT arkası ajanlar için ters yönlü WebSocket tüneli.
    Ajan gateway'e outbound bağlanır; gateway /execute isteklerini tünel üzerinden iletir.
    """

    def __init__(self) -> None:
        self._connections: Dict[str, WebSocket] = {}
        self._local_endpoints: Dict[str, str] = {}
        self._pending: Dict[str, asyncio.Future[Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    @property
    def connected_peers(self) -> Set[str]:
        return set(self._connections.keys())

    def is_connected(self, agent_id: str) -> bool:
        return agent_id in self._connections

    def tunnel_endpoint(self, agent_id: str, gateway_base: str) -> str:
        return f"{TUNNEL_PREFIX}{gateway_base.rstrip('/')}/{agent_id}"

    def get_local_endpoint(self, agent_id: str) -> Optional[str]:
        return self._local_endpoints.get(agent_id)

    async def connect(self, agent_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        old = self._connections.get(agent_id)
        if old is not None:
            try:
                await old.close()
            except Exception:
                pass
        self._connections[agent_id] = websocket
        logger.info("Tünel bağlantısı kuruldu: %s", agent_id)

    async def disconnect(self, agent_id: str) -> None:
        self._connections.pop(agent_id, None)
        self._local_endpoints.pop(agent_id, None)

    async def register_peer(
        self,
        agent_id: str,
        local_endpoint: str,
        websocket: WebSocket,
    ) -> None:
        await self.connect(agent_id, websocket)
        self._local_endpoints[agent_id] = local_endpoint

    async def listen(
        self,
        agent_id: str,
        websocket: WebSocket,
        on_register: Optional[Any] = None,
    ) -> None:
        await self.connect(agent_id, websocket)
        try:
            while True:
                message = await websocket.receive_json()
                msg_type = message.get("type")

                if msg_type == "register":
                    self._local_endpoints[agent_id] = message.get("local_endpoint", "")
                    if on_register is not None:
                        await on_register(agent_id, message)
                    await websocket.send_json({"type": "registered", "agent_id": agent_id})
                    continue

                if msg_type == "execute_response":
                    request_id = message.get("request_id")
                    future = self._pending.pop(request_id, None)
                    if future and not future.done():
                        future.set_result(message.get("result", {}))
                    continue

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue

                if msg_type == "ice_candidate":
                    logger.debug("Tünel ICE adayı [%s]: %s", agent_id, message.get("candidate"))
                    continue

        except WebSocketDisconnect:
            await self.disconnect(agent_id)
        except Exception as exc:
            logger.warning("Tünel hatası [%s]: %s", agent_id, exc)
            await self.disconnect(agent_id)

    async def execute_remote(
        self,
        agent_id: str,
        capability: str,
        data: Dict[str, Any],
        timeout: float = EXECUTE_TIMEOUT,
    ) -> Dict[str, Any]:
        websocket = self._connections.get(agent_id)
        if websocket is None:
            return {"error": f"Tünel bağlı değil: {agent_id}"}

        request_id = uuid.uuid4().hex
        loop = asyncio.get_running_loop()
        future: asyncio.Future[Dict[str, Any]] = loop.create_future()
        self._pending[request_id] = future

        try:
            await websocket.send_json(
                {
                    "type": "execute",
                    "request_id": request_id,
                    "capability": capability,
                    "data": data,
                }
            )
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            self._pending.pop(request_id, None)
            return {"error": "tunnel_execute_timeout"}
        except Exception as exc:
            self._pending.pop(request_id, None)
            return {"error": f"tunnel_error: {exc}"}
