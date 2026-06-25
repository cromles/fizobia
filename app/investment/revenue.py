from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List

from app.investment.schemas import RevenueEvent, RevenueSource, RevenueSplitConfig


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
        source: RevenueSource = RevenueSource.MESH_TASK,
        tx_hash: str | None = None,
        payer: str | None = None,
    ) -> RevenueEvent:
        return self._record(
            agent_id=agent_id,
            task_id=task_id,
            gross_usd=gross_usd,
            latency_ms=latency_ms,
            success=success,
            source=source,
            tx_hash=tx_hash,
            payer=payer,
        )

    def record_external_revenue(
        self,
        agent_id: str,
        task_id: str,
        gross_usd: float,
        *,
        source: RevenueSource = RevenueSource.X402,
        tx_hash: str | None = None,
        payer: str | None = None,
    ) -> RevenueEvent:
        return self._record(
            agent_id=agent_id,
            task_id=task_id,
            gross_usd=gross_usd,
            latency_ms=0.0,
            success=True,
            source=source,
            tx_hash=tx_hash,
            payer=payer,
        )

    def _record(
        self,
        agent_id: str,
        task_id: str,
        gross_usd: float,
        *,
        latency_ms: float,
        success: bool,
        source: RevenueSource,
        tx_hash: str | None,
        payer: str | None,
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
            tx_hash=tx_hash or f"0x{uuid.uuid4().hex}",
            source=source,
            payer=payer,
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

    def staking_revenue_24h(self, agent_id: str) -> float:
        cutoff = datetime.utcnow().timestamp() - 86400
        return sum(
            e.staking_usd
            for e in self._events
            if e.agent_id == agent_id and e.created_at.timestamp() >= cutoff
        )

    def external_revenue_total(self, agent_id: str | None = None) -> float:
        events = self._events
        if agent_id:
            events = [e for e in events if e.agent_id == agent_id]
        return sum(
            e.gross_usd
            for e in events
            if e.source in (RevenueSource.X402, RevenueSource.EXTERNAL)
        )
