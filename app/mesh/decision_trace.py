"""Karar izi — hangi ajan, bütçe, health_score ile ne karar verildi."""

from __future__ import annotations

import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional

MAX_TRACES = 300


@dataclass
class DecisionTrace:
    trace_id: str
    decision: str
    agent_id: str
    pipeline: str
    health_score: float
    budget_usd: float
    allowed: bool
    reason: str
    extra: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_public(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "decision": self.decision,
            "agent_id": self.agent_id,
            "pipeline": self.pipeline,
            "health_score": round(self.health_score, 4),
            "budget_usd": round(self.budget_usd, 6),
            "allowed": self.allowed,
            "reason": self.reason,
            "extra": self.extra,
            "timestamp": self.timestamp,
        }


_traces: Deque[DecisionTrace] = deque(maxlen=MAX_TRACES)


def trace_decision(
    decision: str,
    *,
    agent_id: str = "",
    pipeline: str = "",
    health_score: float = 0.0,
    budget_usd: float = 0.0,
    allowed: bool = True,
    reason: str = "",
    extra: Optional[Dict[str, Any]] = None,
) -> DecisionTrace:
    rec = DecisionTrace(
        trace_id=f"tr_{uuid.uuid4().hex[:10]}",
        decision=decision,
        agent_id=agent_id,
        pipeline=pipeline,
        health_score=health_score,
        budget_usd=budget_usd,
        allowed=allowed,
        reason=reason,
        extra=extra or {},
    )
    _traces.appendleft(rec)
    return rec


def get_decision_traces(*, limit: int = 30) -> List[Dict[str, Any]]:
    return [t.to_public() for t in list(_traces)[:limit]]


def reset_decision_traces() -> None:
    _traces.clear()
