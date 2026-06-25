from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

from app.config import settings
from app.core.router import OpenAgentMeshRouter
from app.investment.live import count_reachable_agents

logger = logging.getLogger(__name__)

_LIVE_GOALS: List[Tuple[str, Dict[str, Any]]] = [
    ("BioMed literatür taraması yap", {"query": "kardiyovasküler RCT meta-analizi"}),
    ("finansal risk özeti sentezle", {"query": "ETH volatilite ve likidite"}),
    ("ham veriyi normalize et", {"raw_text": "OAM ağı canlı iş akışı — şema dönüşümü"}),
    ("piyasa momentum analizi yap", {"query": "BTC dominance ve altcoin rotasyonu"}),
    ("haber sentiment skoru üret", {"text": "Fed faiz kararı piyasa etkisi"}),
    ("web kaynağından veri çek", {"url": "https://mesh.oam/market-data"}),
    ("yatırımcı raporu sentezle", {"topic": "Q2 dijital varlık portföy özeti"}),
    ("uyumluluk kontrolü çalıştır", {"payload": "transaction_batch_8842"}),
    ("çok adımlı pipeline planla", {"goal": "fetch-analyze-report pipeline"}),
    ("çıktı kalitesini doğrula", {"text": "pipeline output checksum"}),
]


class HubActivityWorker:
    """
    Demo kapalıyken ağda gerçek görevler çalıştırır.
    mesh/run → router → investment hub gelir kaydı → canlı aktivite akışı.
    """

    def __init__(self, router: OpenAgentMeshRouter) -> None:
        self.router = router
        self._task: Any = None
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
        import asyncio

        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            "Hub activity worker başladı (her %ss gerçek görev, %d hedef)",
            settings.hub_live_interval,
            len(_LIVE_GOALS),
        )

    async def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except Exception:
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
        import asyncio

        await asyncio.sleep(8.0)
        while self._running:
            reachable = count_reachable_agents(self.router.list_agents())
            if reachable == 0:
                logger.info(
                    "Hub activity worker: çevrimiçi ajan yok — görev atlanıyor "
                    "(tam mesh için: python3 -m app.run_stack)"
                )
                await asyncio.sleep(settings.hub_live_interval)
                continue
            try:
                await self.run_once()
            except Exception as exc:
                logger.warning("Hub live görev hatası: %s", exc)
            await asyncio.sleep(settings.hub_live_interval)
