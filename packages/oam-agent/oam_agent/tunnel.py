from __future__ import annotations

import asyncio
import inspect
import json
import logging
from typing import Any, Awaitable, Callable, Dict, Optional, Union

import httpx
import websockets

from oam_agent.schemas import AgentManifest

logger = logging.getLogger(__name__)

Handler = Callable[[Dict[str, Any]], Union[Dict[str, Any], Awaitable[Dict[str, Any]]]]


class MeshTunnelClient:
    """
    NAT arkası ajan — gateway'e ters WebSocket tüneli açar.
    Gateway /execute isteklerini bu tünel üzerinden ajana iletir.
    """

    def __init__(self, gateway_url: str, agent_id: str) -> None:
        self.gateway_url = gateway_url.rstrip("/")
        self.agent_id = agent_id
        self._handlers: Dict[str, Handler] = {}
        self._running = False

    def register_handler(self, capability: str, handler: Handler) -> None:
        self._handlers[capability] = handler

    def _tunnel_ws_url(self) -> str:
        base = self.gateway_url.replace("https://", "wss://").replace("http://", "ws://")
        return f"{base}/network/tunnel/{self.agent_id}"

    async def connect_and_serve(
        self,
        manifest: AgentManifest,
        local_endpoint: str,
    ) -> None:
        ws_url = self._tunnel_ws_url()
        logger.info("Tünel bağlanıyor: %s", ws_url)
        self._running = True

        while self._running:
            try:
                async with websockets.connect(ws_url, ping_interval=20) as websocket:
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "register",
                                "local_endpoint": local_endpoint,
                                "manifest": manifest.model_dump(),
                            }
                        )
                    )
                    reg_ack = json.loads(await websocket.recv())
                    logger.info("Tünel kaydı: %s", reg_ack)

                    while self._running:
                        raw = await websocket.recv()
                        message = json.loads(raw)
                        if message.get("type") != "execute":
                            continue
                        capability = message.get("capability", "")
                        data = message.get("data", {})
                        request_id = message.get("request_id", "")
                        handler = self._handlers.get(capability)
                        if handler is None:
                            result = {"error": f"unknown_capability:{capability}"}
                        else:
                            try:
                                output = handler(data)
                                if inspect.isawaitable(output):
                                    output = await output
                                result = output if isinstance(output, dict) else {"error": "invalid_handler_output"}
                            except Exception as exc:
                                result = {"error": str(exc)}
                        await websocket.send(
                            json.dumps(
                                {
                                    "type": "execute_response",
                                    "request_id": request_id,
                                    "result": result,
                                }
                            )
                        )
            except Exception as exc:
                logger.warning("Tünel koptu [%s], yeniden bağlanılıyor: %s", self.agent_id, exc)
                await asyncio.sleep(3)

    def stop(self) -> None:
        self._running = False
