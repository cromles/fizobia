"""Geri besleme — başarısızlık hafızası, beyin ajanları deneyimle öğrenir."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional

from app.mesh.cellular_taxonomy import BRAIN_AGENT_IDS

MAX_FAILURES = 200


@dataclass
class FailureRecord:
    record_id: str
    agent_id: str
    pipeline: str
    error: str
    context: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

    def to_public(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "agent_id": self.agent_id,
            "pipeline": self.pipeline,
            "error": self.error[:300],
            "context": self.context,
            "timestamp": self.timestamp,
        }


_failures: Deque[FailureRecord] = deque(maxlen=MAX_FAILURES)
_success_streak: Dict[str, int] = {}


def record_failure(
    *,
    agent_id: str,
    error: str,
    pipeline: str = "",
    context: Optional[Dict[str, Any]] = None,
) -> FailureRecord:
    import uuid

    rec = FailureRecord(
        record_id=f"fb_{uuid.uuid4().hex[:8]}",
        agent_id=agent_id,
        pipeline=pipeline,
        error=error,
        context=context or {},
    )
    _failures.appendleft(rec)
    _success_streak[agent_id] = 0
    return rec


def record_success(agent_id: str) -> None:
    _success_streak[agent_id] = _success_streak.get(agent_id, 0) + 1


def record_pipeline_feedback(
    *,
    agent_ids: List[str],
    pipeline: str,
    success: bool,
    error: str = "",
    detail: Optional[Dict[str, Any]] = None,
) -> None:
    if success:
        for aid in agent_ids:
            record_success(aid)
        return
    primary = agent_ids[0] if agent_ids else "oam.orchestrator.pipeline.local"
    record_failure(
        agent_id=primary,
        error=error or f"{pipeline} başarısız",
        pipeline=pipeline,
        context={"agents": agent_ids, **(detail or {})},
    )


def get_recent_failures(*, limit: int = 15, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
    items = list(_failures)
    if agent_id:
        items = [f for f in items if f.agent_id == agent_id]
    return [f.to_public() for f in items[:limit]]


def summarize_for_brain() -> str:
    """Beyin hücreleri bir sonraki kararda kullanır."""
    if not _failures:
        return "Geri besleme temiz — son başarısızlık yok."
    recent = list(_failures)[:5]
    parts = []
    for f in recent:
        parts.append(f"{f.pipeline or 'görev'}: {f.error[:80]}")
    return "Son hatalar → " + " · ".join(parts)


def get_brain_feedback() -> Dict[str, Any]:
    brain_failures = [
        f.to_public()
        for f in _failures
        if f.agent_id in BRAIN_AGENT_IDS
    ][:10]
    return {
        "summary": summarize_for_brain(),
        "recent_failures": get_recent_failures(limit=12),
        "brain_agent_failures": brain_failures,
        "success_streaks": dict(_success_streak),
        "total_failures_logged": len(_failures),
    }


def reset_feedback() -> None:
    _failures.clear()
    _success_streak.clear()
