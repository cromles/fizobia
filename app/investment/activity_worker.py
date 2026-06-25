from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Tuple

from app.config import settings
from app.core.router import OpenAgentMeshRouter

logger = logging.getLogger(__name__)

_LIVE_GOALS: List[Tuple[str, Dict[str, Any]]] = [
    ("BioMed literatür taraması yap", {"query": "kardiyovasküler RCT meta-analizi"}),
    ("finansal risk özeti sentezle", {"query": "ETH volatilite ve likidite"}),
    ("ham veriyi normalize et", {"raw_text": "OAM ağı canlı iş akışı — şema dönüşümü"}),
]


class HubActivityWorker:
    """
    Demo kapalıyken ağda gerçek görevler çalıştırır.
    mesh/run → router → investment hub gelir kaydı → canlı aktivite akışı.
    """

    def __init__(self, router: OpenAgentMeshRouter) -> None:
        self.router = router
        self._task: asyncio.Task[None] | None = None
        self._running = False
        self._goal_index = 0

    async def start(self) -> None:
        if settings.hub_demo_mode:
            logger.info("Hub activity worker: demo modu — otomatik görev kapalı")
            return
        if settings.hub_live_interval <= 0:
            logger.info("Hub activity worker: interval=0 — kapalı")
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            "Hub activity worker başladı (her %ss gerçek görev)",
            settings.hub_live_interval,
        )

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def run_once(self) -> Dict[str, Any]:
        goal, data = _LIVE_GOALS[self._goal_index % len(_LIVE_GOALS)]
        self._goal_index += 1
        logger.info("[Hub Live] Görev: %s", goal)
        result = await self.router.run_goal(goal, data)
        return {
            "goal": goal,
            "plan_id": result.plan_id,
            "tasks": len(result.task_results),
            "proofs": result.proof_of_execution,
        }

    async def _run_loop(self) -> None:
        await asyncio.sleep(8.0)
        while self._running:
            try:
                await self.run_once()
            except Exception as exc:
                logger.warning("Hub live görev hatası: %s", exc)
            await asyncio.sleep(settings.hub_live_interval)
