from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Any, Awaitable, Callable, Dict, Optional, Union

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException

from oam_agent.schemas import AgentCapability, AgentManifest, ExecuteRequest

logger = logging.getLogger(__name__)

Handler = Union[
    Callable[[Dict[str, Any]], Dict[str, Any]],
    Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]],
]


class OAMAgent:
    """
    OAM protokolüne uygun ajan sunucusu.
    /execute ve /manifest endpoint'lerini otomatik yayınlar.
    """

    def __init__(
        self,
        agent_id: str,
        endpoint: str,
        cost_per_token: float = 0.0,
        reliability_score: float = 1.0,
    ) -> None:
        self.manifest = AgentManifest(
            agent_id=agent_id,
            endpoint=endpoint.rstrip("/"),
            cost_per_token=cost_per_token,
            reliability_score=reliability_score,
            capabilities=[],
        )
        self._handlers: Dict[str, Handler] = {}
        self.app = FastAPI(title=f"OAM Agent: {agent_id}")
        self._mount_routes()

    def capability(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        output_schema: Dict[str, Any],
    ) -> Callable[[Handler], Handler]:
        def decorator(func: Handler) -> Handler:
            if name in self._handlers:
                raise ValueError(f"Capability already registered: {name}")
            self.manifest.capabilities.append(
                AgentCapability(
                    name=name,
                    description=description,
                    input_schema=input_schema,
                    output_schema=output_schema,
                )
            )
            self._handlers[name] = func
            return func

        return decorator

    def _mount_routes(self) -> None:
        @self.app.get("/manifest")
        async def get_manifest() -> AgentManifest:
            return self.manifest

        @self.app.get("/health")
        async def health() -> Dict[str, str]:
            return {"status": "ok", "agent_id": self.manifest.agent_id}

        @self.app.post("/execute")
        async def execute(request: ExecuteRequest) -> Dict[str, Any]:
            handler = self._handlers.get(request.capability)
            if handler is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Unknown capability: {request.capability}",
                )
            result = handler(request.data)
            if inspect.isawaitable(result):
                result = await result
            if not isinstance(result, dict):
                raise HTTPException(status_code=500, detail="Handler must return dict")
            return result

    async def join_mesh(
        self,
        gateway_url: str,
        *,
        announce: bool = True,
        heartbeat_interval: Optional[float] = 30.0,
    ) -> None:
        client = MeshClient(gateway_url)
        await client.register(self.manifest)
        if announce:
            await client.announce(self.manifest)
        if heartbeat_interval and heartbeat_interval > 0:
            asyncio.create_task(
                client.heartbeat_loop(
                    self.manifest,
                    interval=heartbeat_interval,
                    announce=announce,
                )
            )

    def run(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        uvicorn.run(self.app, host=host, port=port)


class MeshClient:
    """OAM gateway ile konuşan istemci — kayıt ve DHT duyurusu."""

    def __init__(self, gateway_url: str, timeout: float = 10.0) -> None:
        self.gateway_url = gateway_url.rstrip("/")
        self.timeout = timeout

    async def register(
        self,
        manifest: AgentManifest,
        *,
        upsert: bool = False,
    ) -> Dict[str, Any]:
        path = "/agents/register"
        if upsert:
            path = f"{path}?upsert=true"
        return await self._post(path, {"manifest": manifest.model_dump()})

    async def announce(self, manifest: AgentManifest, ttl: int = 60) -> Dict[str, Any]:
        return await self._post(
            "/discovery/announce",
            {"manifest": manifest.model_dump(), "ttl": ttl},
        )

    async def announce_public(
        self,
        manifest: AgentManifest,
        local_endpoint: str,
        public_endpoint: str | None = None,
        ice_candidates: list[str] | None = None,
        ttl: int = 120,
    ) -> Dict[str, Any]:
        """NAT arkasından küresel DHT havuzuna duyuru."""
        return await self._post(
            "/network/announce",
            {
                "manifest": manifest.model_dump(),
                "local_endpoint": local_endpoint,
                "public_endpoint": public_endpoint,
                "ice_candidates": ice_candidates or [],
                "ttl": ttl,
            },
        )

    async def fetch_stun_config(self) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.gateway_url}/network/stun")
            response.raise_for_status()
            return response.json()

    async def heartbeat_loop(
        self,
        manifest: AgentManifest,
        interval: float = 30.0,
        announce: bool = True,
    ) -> None:
        while True:
            await asyncio.sleep(interval)
            try:
                if announce:
                    await self.announce(manifest)
                else:
                    await self.register(manifest)
            except Exception as exc:
                logger.warning("OAM heartbeat başarısız [%s]: %s", manifest.agent_id, exc)

    async def _post(
        self,
        path: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.gateway_url}{path}", json=payload)
            response.raise_for_status()
            return response.json()
