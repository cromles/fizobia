"""Metabolizma — ajan başına enerji harcaması ve gelir dengesi."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from app.mesh.cellular_taxonomy import (
    CELL_BRAIN,
    CELL_IMMUNE,
    CELL_MUSCLE,
    CELL_SENSORY,
    cell_type_for,
)
from app.mesh.homeostasis import credit_energy, debit_energy, organism_energy

# Hücre tipine göre API/görev maliyeti (USD eşdeğeri)
CELL_API_COST_USD: Dict[str, float] = {
    CELL_SENSORY: 0.0012,
    CELL_BRAIN: 0.0025,
    CELL_MUSCLE: 0.0060,
    CELL_IMMUNE: 0.0018,
}

STARVATION_NET_USD = -0.05


@dataclass
class AgentMetabolism:
    agent_id: str
    cell_type: str
    spent_usd: float = 0.0
    earned_usd: float = 0.0
    api_calls: int = 0
    starving: bool = False
    energy_save_mode: bool = False
    updated_at: float = field(default_factory=time.time)

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
            "starving": self.starving,
            "energy_save_mode": self.energy_save_mode,
            "updated_at": self.updated_at,
        }


_metabolism: Dict[str, AgentMetabolism] = {}
_total_spent: float = 0.0
_total_earned: float = 0.0


def _record(agent_id: str) -> AgentMetabolism:
    if agent_id not in _metabolism:
        _metabolism[agent_id] = AgentMetabolism(
            agent_id=agent_id,
            cell_type=cell_type_for(agent_id),
        )
    return _metabolism[agent_id]


def record_api_spend(agent_id: str, *, cost_usd: Optional[float] = None) -> AgentMetabolism:
    global _total_spent
    cell = cell_type_for(agent_id)
    cost = cost_usd if cost_usd is not None else CELL_API_COST_USD.get(cell, 0.002)
    row = _record(agent_id)
    row.spent_usd += cost
    row.api_calls += 1
    row.updated_at = time.time()
    row.starving = row.net_usd <= STARVATION_NET_USD
    row.energy_save_mode = row.starving or organism_energy() < 5.0
    _total_spent += cost
    debit_energy(cost, reason=f"api:{agent_id}")
    return row


def record_agent_revenue(agent_id: str, amount_usd: float, *, reason: str = "x402") -> AgentMetabolism:
    global _total_earned
    if amount_usd <= 0:
        return _record(agent_id)
    row = _record(agent_id)
    row.earned_usd += amount_usd
    row.updated_at = time.time()
    row.starving = row.net_usd <= STARVATION_NET_USD
    row.energy_save_mode = row.starving
    _total_earned += amount_usd
    credit_energy(amount_usd, reason=reason)
    return row


def record_pipeline_metabolism(
    agent_ids: List[str],
    *,
    success: bool,
    revenue_usd: float = 0.0,
) -> List[Dict[str, Any]]:
    """Pipeline sonrası tüm işçi hücrelerinin metabolizmasını güncelle."""
    results: List[Dict[str, Any]] = []
    share = revenue_usd / max(len(agent_ids), 1) if revenue_usd > 0 else 0.0
    for aid in agent_ids:
        record_api_spend(aid)
        if success and share > 0:
            record_agent_revenue(aid, share)
        results.append(_record(aid).to_public())
    return results


def can_agent_act(agent_id: str) -> Tuple[bool, str]:
    from app.mesh.homeostasis import cell_type_allowed

    cell = cell_type_for(agent_id)
    if not cell_type_allowed(cell):
        return False, f"Homeostazi — {cell} hücresi şu an kısıtlı"
    row = _record(agent_id)
    if row.starving and cell == CELL_MUSCLE:
        return False, "Metabolizma — kas hücresi açlık modunda (net negatif)"
    return True, "ok"


def get_metabolism_status() -> Dict[str, Any]:
    agents = sorted(_metabolism.values(), key=lambda r: r.net_usd)
    starving = [a.to_public() for a in agents if a.starving]
    return {
        "organism_energy_usd": organism_energy(),
        "total_spent_usd": round(_total_spent, 6),
        "total_earned_usd": round(_total_earned, 6),
        "net_usd": round(_total_earned - _total_spent, 6),
        "cell_costs_usd": CELL_API_COST_USD,
        "starvation_threshold_net_usd": STARVATION_NET_USD,
        "agents": [a.to_public() for a in sorted(_metabolism.values(), key=lambda x: -x.spent_usd)],
        "starving_agents": starving,
        "starving_count": len(starving),
    }


def reset_metabolism() -> None:
    global _total_spent, _total_earned
    _metabolism.clear()
    _total_spent = 0.0
    _total_earned = 0.0
