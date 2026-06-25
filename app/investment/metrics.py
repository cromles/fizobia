from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from app.investment.schemas import AgentHealthMetrics


@dataclass
class _RevenuePoint:
    amount_usd: float
    timestamp: float


@dataclass
class _AgentRuntime:
    total_calls: int = 0
    successful_calls: int = 0
    total_latency_ms: float = 0.0
    revenue_points: List[_RevenuePoint] = field(default_factory=list)


class MetricsCollector:
    """Ağ sağlık metrikleri — başarı oranı, gecikme, çağrı sayısı."""

    WINDOW_24H = 86400.0

    def __init__(self) -> None:
        self._agents: Dict[str, _AgentRuntime] = defaultdict(_AgentRuntime)

    def record_execution(
        self,
        agent_id: str,
        *,
        success: bool,
        latency_ms: float,
        revenue_usd: float = 0.0,
    ) -> None:
        runtime = self._agents[agent_id]
        runtime.total_calls += 1
        if success:
            runtime.successful_calls += 1
        runtime.total_latency_ms += latency_ms
        if revenue_usd > 0:
            runtime.revenue_points.append(
                _RevenuePoint(amount_usd=revenue_usd, timestamp=time.time())
            )

    def get_health(self, agent_id: str, reliability_score: float = 1.0) -> AgentHealthMetrics:
        runtime = self._agents.get(agent_id)
        if runtime is None or runtime.total_calls == 0:
            return AgentHealthMetrics(
                success_rate=reliability_score,
                avg_latency_ms=0.0,
                total_calls=0,
                successful_calls=0,
            )

        measured_rate = runtime.successful_calls / runtime.total_calls
        blended = 0.7 * reliability_score + 0.3 * measured_rate
        avg_latency = runtime.total_latency_ms / runtime.total_calls
        return AgentHealthMetrics(
            success_rate=round(min(blended, 1.0), 4),
            avg_latency_ms=round(avg_latency, 2),
            total_calls=runtime.total_calls,
            successful_calls=runtime.successful_calls,
        )

    def volume_24h(self, agent_id: str) -> float:
        runtime = self._agents.get(agent_id)
        if runtime is None:
            return 0.0
        cutoff = time.time() - self.WINDOW_24H
        return sum(p.amount_usd for p in runtime.revenue_points if p.timestamp >= cutoff)

    def prune_old_points(self, max_age_seconds: float = WINDOW_24H * 2) -> None:
        cutoff = time.time() - max_age_seconds
        for runtime in self._agents.values():
            runtime.revenue_points = [
                p for p in runtime.revenue_points if p.timestamp >= cutoff
            ]
