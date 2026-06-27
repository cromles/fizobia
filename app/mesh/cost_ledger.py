"""Maliyet defteri — her API çağrısı: cost_usd, agent_id, timestamp, success."""

from __future__ import annotations

import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional, Tuple

from app.mesh.backpressure import credit_budget, debit_budget, budget_usd, health_score
from app.mesh.cellular_taxonomy import CELL_MUSCLE, cell_type_for
from app.mesh.backpressure import worker_type_allowed

WORKER_API_COST_USD: Dict[str, float] = {
    "sensory": 0.0012,
    "brain": 0.0025,
    "muscle": 0.0060,
    "immune": 0.0018,
}

BUDGET_EXHAUSTED_NET_USD = -0.05
MAX_LEDGER = 500


@dataclass
class CostLedgerEntry:
    entry_id: str
    agent_id: str
    cost_usd: float
    operation: str
    success: bool
    timestamp: float = field(default_factory=time.time)

    def to_public(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "agent_id": self.agent_id,
            "cost_usd": round(self.cost_usd, 6),
            "operation": self.operation,
            "success": self.success,
            "timestamp": self.timestamp,
        }


@dataclass
class AgentCostSummary:
    agent_id: str
    cell_type: str
    spent_usd: float = 0.0
    earned_usd: float = 0.0
    api_calls: int = 0
    budget_exhausted: bool = False

    @property
    def net_usd(self) -> float:
        return self.earned_usd - self.spent_usd

    def to_public(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "cell_type": self.cell_type,
            "spent_usd": round(self.spent_usd, 6),
            "earned_usd": round(self.earned_usd, 6),
            "net_usd": round(self.net_usd, 6),
            "api_calls": self.api_calls,
            "budget_exhausted": self.budget_exhausted,
        }


_ledger: Deque[CostLedgerEntry] = deque(maxlen=MAX_LEDGER)
_summaries: Dict[str, AgentCostSummary] = {}
_total_spent: float = 0.0
_total_earned: float = 0.0


def _summary(agent_id: str) -> AgentCostSummary:
    if agent_id not in _summaries:
        _summaries[agent_id] = AgentCostSummary(
            agent_id=agent_id,
            cell_type=cell_type_for(agent_id),
        )
    return _summaries[agent_id]


def record_cost(
    agent_id: str,
    *,
    cost_usd: Optional[float] = None,
    operation: str = "api_call",
    success: bool = True,
) -> CostLedgerEntry:
    global _total_spent
    cell = cell_type_for(agent_id)
    cost = cost_usd if cost_usd is not None else WORKER_API_COST_USD.get(cell, 0.002)
    entry = CostLedgerEntry(
        entry_id=f"cost_{uuid.uuid4().hex[:10]}",
        agent_id=agent_id,
        cost_usd=cost,
        operation=operation,
        success=success,
    )
    _ledger.appendleft(entry)
    row = _summary(agent_id)
    row.spent_usd += cost
    row.api_calls += 1
    row.budget_exhausted = row.net_usd <= BUDGET_EXHAUSTED_NET_USD
    _total_spent += cost
    debit_budget(cost, reason=f"{operation}:{agent_id}")
    return entry


def record_revenue(agent_id: str, amount_usd: float, *, operation: str = "x402") -> None:
    global _total_earned
    if amount_usd <= 0:
        return
    row = _summary(agent_id)
    row.earned_usd += amount_usd
    row.budget_exhausted = row.net_usd <= BUDGET_EXHAUSTED_NET_USD
    _total_earned += amount_usd
    credit_budget(amount_usd, reason=operation)


def record_pipeline_costs(
    agent_ids: List[str],
    *,
    success: bool,
    revenue_usd: float = 0.0,
) -> List[Dict[str, Any]]:
    share = revenue_usd / max(len(agent_ids), 1) if revenue_usd > 0 else 0.0
    for aid in agent_ids:
        record_cost(aid, operation="pipeline", success=success)
        if success and share > 0:
            record_revenue(aid, share)
    return [_summary(aid).to_public() for aid in agent_ids]


def can_worker_run(agent_id: str) -> Tuple[bool, str]:
    cell = cell_type_for(agent_id)
    ok, reason = worker_type_allowed(cell)
    if not ok:
        return False, reason
    row = _summary(agent_id)
    if row.budget_exhausted and cell == CELL_MUSCLE:
        return False, f"budget_exhausted: agent {agent_id} net={row.net_usd:.4f}"
    if health_score() <= 0.05:
        return False, f"budget_exhausted: global health={health_score():.3f}"
    return True, "ok"


def get_cost_ledger_status(*, limit: int = 50) -> Dict[str, Any]:
    exhausted = [s.to_public() for s in _summaries.values() if s.budget_exhausted]
    return {
        "budget_usd": budget_usd(),
        "health_score": health_score(),
        "total_spent_usd": round(_total_spent, 6),
        "total_earned_usd": round(_total_earned, 6),
        "net_usd": round(_total_earned - _total_spent, 6),
        "worker_api_cost_usd": WORKER_API_COST_USD,
        "budget_exhausted_threshold_net_usd": BUDGET_EXHAUSTED_NET_USD,
        "entries": [e.to_public() for e in list(_ledger)[:limit]],
        "agents": [s.to_public() for s in sorted(_summaries.values(), key=lambda x: -x.spent_usd)],
        "budget_exhausted_agents": exhausted,
        "budget_exhausted_count": len(exhausted),
    }


def reset_cost_ledger() -> None:
    global _total_spent, _total_earned
    _ledger.clear()
    _summaries.clear()
    _total_spent = 0.0
    _total_earned = 0.0
