from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List

from app.investment.schemas import AgentHealthMetrics


@dataclass
class _AgentRuntime:
    total_calls: int = 0
    successful_calls: int = 0
    total_latency_ms: float = 0.0
    revenue_events: List[float] = field(default_factory=list)


class MetricsCollector:
    """Ağ sağlık metrikleri — başarı oranı, gecikme, çağrı sayısı."""

    def __init__(self) -> None:
        self._agents: Dict[str, _AgentRuntime] = defaultdict(_AgentRuntime)
        self._window_start = time.time()

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
            runtime.revenue_events.append(revenue_usd)

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
        return sum(runtime.revenue_events)
