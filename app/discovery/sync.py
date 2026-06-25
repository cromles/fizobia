from __future__ import annotations

import asyncio
import logging
from typing import Optional

from app.discovery.base import PeerDiscovery
from app.registry.agent_registry import AgentRegistry

logger = logging.getLogger(__name__)


class DiscoverySync:
    """DHT'deki canlı ajanları gateway registry'sine senkronize eder."""

    def __init__(
        self,
        discovery: PeerDiscovery,
        registry: AgentRegistry,
        interval: float = 30.0,
    ) -> None:
        self.discovery = discovery
        self.registry = registry
        self.interval = interval
        self._task: Optional[asyncio.Task[None]] = None

    def sync_once(self) -> int:
        synced = 0
        for manifest in self.discovery.list_peers():
            if hasattr(self.registry, "upsert"):
                self.registry.upsert(manifest)
            else:
                self.registry.register(manifest)
            synced += 1
        logger.info("Discovery sync tamamlandı: %s ajan", synced)
        return synced

    async def start(self) -> None:
        if self.interval <= 0:
            return
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self) -> None:
        while True:
            try:
                self.sync_once()
            except Exception as exc:
                logger.warning("Discovery sync hatası: %s", exc)
            await asyncio.sleep(self.interval)
