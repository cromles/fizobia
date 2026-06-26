"""7/24 mesh otopilot — kurucu emriyle otomatik mesh proof ve işe alma döngüsü."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.config import settings
from app.mesh.founders import ORCHESTRATOR_ID
from app.mesh.hierarchy import announce_chain_of_command, autopilot_cycle_order
from app.mesh.proof_pipeline import MESH_PROOF_AGENTS

logger = logging.getLogger(__name__)

_AUTOPILOT_SYMBOLS: List[str] = ["bitcoin", "ethereum", "solana", "bitcoin"]


class MeshAutopilot:
    """
    Kurucu → Baş Yardımcı → Koordinatör zinciriyle periyodik mesh proof.
    Demo kapalı ve ajanlar çevrimiçiyken durmadan çalışır.
    """

    def __init__(self, router: Any) -> None:
        self.router = router
        self._task: Any = None
        self._running = False
        self._cycles = 0
        self._last_result: Optional[Dict[str, Any]] = None
        self._last_error: Optional[str] = None
        self._symbol_index = 0

    @property
    def cycles_completed(self) -> int:
        return self._cycles

    def status(self) -> Dict[str, Any]:
        return {
            "enabled": settings.hub_autopilot_enabled and not settings.hub_demo_mode,
            "running": self._running,
            "interval_seconds": settings.hub_autopilot_interval,
            "cycles_completed": self._cycles,
            "last_result": self._last_result,
            "last_error": self._last_error,
            "min_reachable_agents": settings.hub_autopilot_min_agents,
        }

    async def start(self) -> None:
        if settings.hub_demo_mode:
            logger.info("Mesh autopilot: demo modu — kapalı")
            return
        if not settings.hub_autopilot_enabled:
            logger.info("Mesh autopilot: devre dışı (OAM_AUTOPILOT_ENABLED=false)")
            return
        if settings.hub_autopilot_interval <= 0:
            logger.info("Mesh autopilot: interval=0 — kapalı")
            return

        import asyncio

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            "Mesh autopilot başladı — her %ss mesh proof (min %d ajan)",
            settings.hub_autopilot_interval,
            settings.hub_autopilot_min_agents,
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

    def _next_symbol(self) -> str:
        symbol = _AUTOPILOT_SYMBOLS[self._symbol_index % len(_AUTOPILOT_SYMBOLS)]
        self._symbol_index += 1
        return symbol

    def _mesh_proof_reachable(self) -> int:
        manifests = self.router.list_agents()
        by_id = {m.agent_id: m for m in manifests}
        count = 0
        for agent_id in MESH_PROOF_AGENTS:
            manifest = by_id.get(agent_id)
            if manifest is None:
                continue
            from app.investment.live import _probe_endpoint

            ok, _ = _probe_endpoint(manifest.endpoint)
            if ok:
                count += 1
        return count

    async def run_cycle(self) -> Dict[str, Any]:
        """Tek otopilot döngüsü — hiyerarşi emri + mesh proof hire."""
        from app.mesh.growth_protocol import get_growth_protocol

        symbol = self._next_symbol()
        self._cycles += 1
        cycle = self._cycles

        announce_chain_of_command()
        order = autopilot_cycle_order(cycle, symbol=symbol)

        growth = get_growth_protocol()
        growth._emit(
            "autopilot_cycle_start",
            f"Otopilot döngü #{cycle} — {symbol} mesh proof",
            agent_id=ORCHESTRATOR_ID,
            detail={"cycle": cycle, "symbol": symbol, "order": order},
        )

        result = await growth.hire_agents(pipeline="mesh_proof", symbol=symbol)
        result["autopilot_cycle"] = cycle
        result["hierarchy_order"] = order

        growth._emit(
            "autopilot_cycle_done",
            f"Otopilot #{cycle} tamam — {result.get('verdict', 'ok')}",
            agent_id=ORCHESTRATOR_ID,
            detail={
                "cycle": cycle,
                "proof_id": result.get("proof_id"),
                "verdict": result.get("verdict"),
            },
        )

        self._last_result = result
        self._last_error = None
        logger.info(
            "[Autopilot] Döngü #%d tamam — proof=%s verdict=%s",
            cycle,
            result.get("proof_id"),
            result.get("verdict"),
        )
        return result

    async def _run_loop(self) -> None:
        import asyncio

        await asyncio.sleep(settings.hub_autopilot_warmup)
        announce_chain_of_command()

        while self._running:
            reachable = self._mesh_proof_reachable()

            if reachable < settings.hub_autopilot_min_agents:
                logger.info(
                    "Mesh autopilot: mesh proof ajanları hazır değil (%d/%d) — "
                    "tam yığın: python3 -m app.run_stack",
                    reachable,
                    len(MESH_PROOF_AGENTS),
                )
                self._last_error = f"agents_unreachable:{reachable}"
                await asyncio.sleep(settings.hub_autopilot_interval)
                continue

            try:
                await self.run_cycle()
            except Exception as exc:
                self._last_error = str(exc)
                logger.warning("Mesh autopilot döngü hatası: %s", exc)

            await asyncio.sleep(settings.hub_autopilot_interval)
