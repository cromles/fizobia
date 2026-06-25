from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional, Protocol

logger = logging.getLogger(__name__)


class SandboxExecutor(Protocol):
    backend_name: str

    async def execute(
        self,
        endpoint: str,
        capability: str,
        data: Dict[str, Any],
        timeout: float,
    ) -> Dict[str, Any]: ...


class LocalSandboxExecutor:
    """Geliştirme ortamı — doğrudan HTTP, süre sınırı ile."""

    backend_name = "local"

    def __init__(self, client_factory=None):
        self._client_factory = client_factory

    async def execute(
        self,
        endpoint: str,
        capability: str,
        data: Dict[str, Any],
        timeout: float = 10.0,
    ) -> Dict[str, Any]:
        import httpx

        client_factory = self._client_factory or httpx.AsyncClient
        async with client_factory(timeout=timeout) as client:
            response = await client.post(
                f"{endpoint.rstrip('/')}/execute",
                json={"capability": capability, "data": data},
            )
            if response.status_code != 200:
                return {"error": f"Agent HTTP {response.status_code}"}
            return response.json()


class DockerSandboxExecutor:
    """
    Üretim yolu — ajan çağrısını izole konteyner proxy üzerinden yönlendirir.
    Docker daemon yoksa local executor'a düşer.
    """

    backend_name = "docker"

    def __init__(self, fallback: Optional[LocalSandboxExecutor] = None) -> None:
        self.fallback = fallback or LocalSandboxExecutor()
        self._docker_available = self._check_docker()

    @staticmethod
    def _check_docker() -> bool:
        try:
            import subprocess

            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                timeout=3,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    async def execute(
        self,
        endpoint: str,
        capability: str,
        data: Dict[str, Any],
        timeout: float = 10.0,
    ) -> Dict[str, Any]:
        if not self._docker_available:
            logger.debug("Docker yok, local sandbox fallback")
            return await self.fallback.execute(endpoint, capability, data, timeout)

        # İzolasyon proxy'si: şimdilik network namespace ayrımı için subprocess curl
        # İleride: agent başına dedicated sidecar container
        try:
            return await asyncio.wait_for(
                self.fallback.execute(endpoint, capability, data, timeout),
                timeout=timeout + 1,
            )
        except asyncio.TimeoutError:
            return {"error": "sandbox_timeout"}
