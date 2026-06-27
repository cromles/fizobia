"""Backpressure — sürekli health_score (0-1) ve kademeli throttling."""

from __future__ import annotations

import time
from typing import Any, Dict, Tuple

from app.mesh.approval_gate import check_approval, evaluate_approval, get_approval_status, grant_approval
from app.mesh.cellular_taxonomy import CELL_BRAIN, CELL_MUSCLE, CELL_SENSORY, PIPELINE_CELL_USAGE
from app.mesh.decision_trace import trace_decision

DEFAULT_BUDGET_USD = 25.0

_budget_usd: float = DEFAULT_BUDGET_USD
_peak_budget_usd: float = DEFAULT_BUDGET_USD


def budget_usd() -> float:
    return round(_budget_usd, 6)


def health_score() -> float:
    """0-1 arası sürekli sağlık — mod sınırı yok."""
    if _peak_budget_usd <= 0:
        return 0.0
    return max(0.0, min(1.0, _budget_usd / _peak_budget_usd))


def throttle_factor() -> float:
    """Kademeli throttling — ani mod geçişi yok."""
    h = health_score()
    if h >= 0.5:
        return 1.0
    if h <= 0.05:
        return 0.0
    # 0.05–0.5 arası yumuşak eğri
    return round((h - 0.05) / 0.45, 4)


def credit_budget(amount_usd: float, *, reason: str = "revenue") -> float:
    global _budget_usd, _peak_budget_usd
    if amount_usd <= 0:
        return _budget_usd
    _budget_usd += amount_usd
    _peak_budget_usd = max(_peak_budget_usd, _budget_usd)
    evaluate_approval(health_score=health_score())
    return _budget_usd


def debit_budget(amount_usd: float, *, reason: str = "api_cost") -> float:
    global _budget_usd
    if amount_usd <= 0:
        return _budget_usd
    _budget_usd = max(0.0, _budget_usd - amount_usd)
    evaluate_approval(health_score=health_score())
    return _budget_usd


def sync_budget_from_revenue(total_revenue_usd: float) -> None:
    global _budget_usd, _peak_budget_usd
    if total_revenue_usd <= 0:
        return
    target = DEFAULT_BUDGET_USD + total_revenue_usd * 0.65
    _budget_usd = max(_budget_usd, min(target, _peak_budget_usd))
    _peak_budget_usd = max(_peak_budget_usd, _budget_usd)
    evaluate_approval(health_score=health_score())


def worker_type_allowed(cell_type: str) -> Tuple[bool, str]:
    h = health_score()
    tf = throttle_factor()
    if h <= 0.05:
        if cell_type not in (CELL_BRAIN, CELL_SENSORY):
            return False, f"budget_critical: health={h:.3f} worker_type={cell_type} blocked"
    if cell_type == CELL_MUSCLE and tf < 0.35:
        return False, f"backpressure: throttle={tf} muscle workers throttled"
    return True, "ok"


def check_pipeline_allowed(pipeline: str) -> Tuple[bool, str]:
    h = health_score()
    tf = throttle_factor()
    cells = PIPELINE_CELL_USAGE.get(pipeline, (CELL_BRAIN, CELL_MUSCLE))

    ok, approval_reason = check_approval()
    if not ok:
        trace_decision(
            "pipeline_blocked",
            pipeline=pipeline,
            health_score=h,
            budget_usd=_budget_usd,
            allowed=False,
            reason=approval_reason,
        )
        return False, approval_reason

    approval_granted = get_approval_status().get("approval_granted", False)

    if h <= 0.05 and not approval_granted:
        trace_decision(
            "pipeline_blocked",
            pipeline=pipeline,
            health_score=h,
            budget_usd=_budget_usd,
            allowed=False,
            reason="budget_exhausted",
        )
        return False, "budget_exhausted: approval gate or budget refill required"

    if not approval_granted:
        if CELL_MUSCLE in cells and tf < 0.2:
            trace_decision(
                "pipeline_blocked",
                pipeline=pipeline,
                health_score=h,
                budget_usd=_budget_usd,
                allowed=False,
                reason=f"backpressure throttle={tf}",
            )
            return False, f"backpressure: throttle={tf} blocks heavy pipeline {pipeline}"

        if pipeline == "arena" and tf < 0.55:
            trace_decision(
                "pipeline_blocked",
                pipeline=pipeline,
                health_score=h,
                budget_usd=_budget_usd,
                allowed=False,
                reason=f"arena throttled at health={h:.3f}",
            )
            return False, f"backpressure: arena throttled (health={h:.3f})"

    trace_decision(
        "pipeline_allowed",
        pipeline=pipeline,
        health_score=h,
        budget_usd=_budget_usd,
        allowed=True,
        reason="ok",
        extra={"throttle_factor": tf},
    )
    return True, "ok"


def get_backpressure_status() -> Dict[str, Any]:
    h = health_score()
    evaluate_approval(health_score=h)
    return {
        "health_score": round(h, 4),
        "throttle_factor": throttle_factor(),
        "budget_usd": budget_usd(),
        "peak_budget_usd": round(_peak_budget_usd, 6),
        "approval": get_approval_status(),
        "updated_at": time.time(),
    }


def reset_backpressure() -> None:
    global _budget_usd, _peak_budget_usd
    from app.mesh.approval_gate import reset_approval_gate

    _budget_usd = DEFAULT_BUDGET_USD
    _peak_budget_usd = DEFAULT_BUDGET_USD
    reset_approval_gate()
