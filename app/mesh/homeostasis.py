"""Geriye uyumluluk — backpressure + approval_gate kullanın."""

from __future__ import annotations

from app.mesh.backpressure import (
    budget_usd as organism_energy,
    check_pipeline_allowed,
    credit_budget as credit_energy,
    debit_budget as debit_energy,
    get_backpressure_status,
    health_score as energy_ratio,
    reset_backpressure,
    sync_budget_from_revenue as sync_energy_from_revenue,
    throttle_factor,
    worker_type_allowed as cell_type_allowed,
)


def compute_mode() -> str:
    """Deprecated — health_score kullanın."""
    h = energy_ratio()
    if h <= 0.05:
        return "critical"
    if h <= 0.30:
        return "hunt"
    if h <= 0.50:
        return "conserve"
    return "normal"


def get_homeostasis_status():
    bp = get_backpressure_status()
    return {
        **bp,
        "mode": compute_mode(),
        "energy_usd": bp["budget_usd"],
        "energy_ratio": bp["health_score"],
        "hitl_required": bp["approval"]["approval_required"],
        "directives": [],
    }


def reset_homeostasis() -> None:
    reset_backpressure()
