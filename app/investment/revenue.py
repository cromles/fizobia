from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List

from app.investment.schemas import RevenueEvent, RevenueSplitConfig


class RevenueLedger:
    """Gerçek zamanlı kâr payı akışı — her görev çalıştırması bir gelir olayı üretir."""

    def __init__(self, split: RevenueSplitConfig | None = None) -> None:
        self.split = split or RevenueSplitConfig()
        self.split.validate_total()
        self._events: List[RevenueEvent] = []
        self._platform_total: float = 0.0
        self._agent_totals: Dict[str, float] = {}

    def record_task_revenue(
        self,
        agent_id: str,
        task_id: str,
        gross_usd: float,
        *,
        latency_ms: float = 0.0,
        success: bool = True,
    ) -> RevenueEvent:
        if gross_usd < 0:
            gross_usd = 0.0

        staking = gross_usd * self.split.staking_share
        platform = gross_usd * self.split.platform_share
        operator = gross_usd * self.split.operator_share

        event = RevenueEvent(
            event_id=uuid.uuid4().hex,
            agent_id=agent_id,
            task_id=task_id,
            gross_usd=round(gross_usd, 8),
            staking_usd=round(staking, 8),
            platform_usd=round(platform, 8),
            operator_usd=round(operator, 8),
            latency_ms=latency_ms,
            success=success,
            created_at=datetime.utcnow(),
            tx_hash=f"0x{uuid.uuid4().hex}",
        )
        self._events.append(event)
        self._platform_total += platform
        self._agent_totals[agent_id] = self._agent_totals.get(agent_id, 0.0) + gross_usd
        return event

    def list_events(self, agent_id: str | None = None, limit: int = 100) -> List[RevenueEvent]:
        events = self._events
        if agent_id:
            events = [e for e in events if e.agent_id == agent_id]
        return events[-limit:]

    def total_revenue(self, agent_id: str) -> float:
        return self._agent_totals.get(agent_id, 0.0)

    def platform_revenue(self) -> float:
        return self._platform_total

    def staking_revenue(self, agent_id: str) -> float:
        return sum(e.staking_usd for e in self._events if e.agent_id == agent_id)
