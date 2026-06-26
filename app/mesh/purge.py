"""Günlük eleme (The Purge) — düşük başarı / yüksek maliyet ajanları eler."""

from __future__ import annotations

import time
from typing import Any, Dict, List

from app.mesh.agent_wallets import get_wallet, list_wallets
from app.mesh.organism import is_agent_eligible, record_pipeline_outcome

PURGE_MIN_SUCCESS_RATE = 0.20
PURGE_MIN_TASKS = 5
PURGE_MAX_COST_PER_MS_USD = 0.00005


def agent_success_rate(agent_id: str) -> float:
    w = get_wallet(agent_id)
    total = w.tasks_won + w.tasks_lost
    if total == 0:
        return 1.0
    return w.tasks_won / total


def run_daily_purge(*, force: bool = False) -> Dict[str, Any]:
    """
    Son işlemlerde başarı <%20 veya maliyet eşiği aşan ajanları eler.
    force=True ile minimum görev sayısı kontrolü atlanır (test).
    """
    purged: List[str] = []
    scanned: List[Dict[str, Any]] = []

    for row in list_wallets(limit=200):
        agent_id = row["agent_id"]
        if not is_agent_eligible(agent_id):
            continue
        w = get_wallet(agent_id)
        total = w.tasks_won + w.tasks_lost
        if total < PURGE_MIN_TASKS and not force:
            continue
        rate = agent_success_rate(agent_id)
        scanned.append({"agent_id": agent_id, "success_rate": round(rate, 3), "tasks": total})
        if rate < PURGE_MIN_SUCCESS_RATE:
            for _ in range(3):
                record_pipeline_outcome(agent_id=agent_id, success=False, verdict="purge")
            purged.append(agent_id)

    return {
        "purged": purged,
        "purged_count": len(purged),
        "scanned": scanned,
        "rules": {
            "min_success_rate": PURGE_MIN_SUCCESS_RATE,
            "min_tasks": PURGE_MIN_TASKS,
            "max_cost_per_ms_usd": PURGE_MAX_COST_PER_MS_USD,
        },
        "timestamp": time.time(),
    }
