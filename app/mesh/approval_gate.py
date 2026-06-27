"""Onay kapısı — düşük bütçe/sağlıkta human-in-the-loop (state machine'den ayrı)."""

from __future__ import annotations

import time
from typing import Any, Dict, Tuple

HEALTH_APPROVAL_THRESHOLD = 0.10

_approval_required: bool = False
_approval_granted: bool = False
_last_reason: str = ""


def evaluate_approval(*, health_score: float) -> None:
    global _approval_required, _last_reason
    if health_score <= HEALTH_APPROVAL_THRESHOLD:
        _approval_required = True
        _last_reason = f"health_score {health_score:.3f} <= {HEALTH_APPROVAL_THRESHOLD}"
    elif _approval_granted:
        _approval_required = False


def grant_approval(*, operator: str = "manual") -> Dict[str, Any]:
    global _approval_granted, _approval_required
    _approval_granted = True
    _approval_required = False
    return {
        "granted": True,
        "operator": operator,
        "timestamp": time.time(),
    }


def revoke_approval() -> None:
    global _approval_granted
    _approval_granted = False


def check_approval() -> Tuple[bool, str]:
    """Pipeline çalışmadan önce onay gerekli mi."""
    if not _approval_required:
        return True, "ok"
    if _approval_granted:
        return True, "approval_granted"
    return False, f"approval_required: {_last_reason}"


def get_approval_status() -> Dict[str, Any]:
    return {
        "approval_required": _approval_required,
        "approval_granted": _approval_granted,
        "threshold_health": HEALTH_APPROVAL_THRESHOLD,
        "reason": _last_reason,
    }


def reset_approval_gate() -> None:
    global _approval_required, _approval_granted, _last_reason
    _approval_required = False
    _approval_granted = False
    _last_reason = ""
