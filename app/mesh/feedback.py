"""Yapılandırılmış geri besleme — hata tipi, kural tabanlı aksiyon."""

from __future__ import annotations

import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional, Tuple

from app.mesh.cellular_taxonomy import BRAIN_AGENT_IDS

MAX_RECORDS = 200
RATE_LIMIT_SKIP_SECONDS = 600
RATE_LIMIT_HIT_THRESHOLD = 3


@dataclass
class FeedbackRecord:
    record_id: str
    agent_id: str
    pipeline: str
    error_type: str
    reason: str
    input_summary: str
    http_status: Optional[int]
    success: bool
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_public(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "agent_id": self.agent_id,
            "pipeline": self.pipeline,
            "error_type": self.error_type,
            "reason": self.reason[:300],
            "input_summary": self.input_summary[:200],
            "http_status": self.http_status,
            "success": self.success,
            "context": self.context,
            "timestamp": self.timestamp,
        }


_records: Deque[FeedbackRecord] = deque(maxlen=MAX_RECORDS)
_success_streak: Dict[str, int] = {}
_skip_until: Dict[str, float] = {}


def classify_error(error: str, http_status: Optional[int] = None) -> str:
    lower = error.lower()
    if http_status == 429 or "429" in lower or "rate limit" in lower:
        return "rate_limit"
    if http_status and http_status >= 500:
        return "upstream_5xx"
    if http_status and 400 <= http_status < 500:
        return "client_4xx"
    if "timeout" in lower:
        return "timeout"
    return "runtime_error"


def record_feedback(
    *,
    agent_id: str,
    pipeline: str,
    success: bool,
    error: str = "",
    input_summary: str = "",
    http_status: Optional[int] = None,
    context: Optional[Dict[str, Any]] = None,
) -> FeedbackRecord:
    error_type = "ok" if success else classify_error(error, http_status)
    rec = FeedbackRecord(
        record_id=f"fb_{uuid.uuid4().hex[:8]}",
        agent_id=agent_id,
        pipeline=pipeline,
        error_type=error_type,
        reason=error or ("ok" if success else "unknown"),
        input_summary=input_summary,
        http_status=http_status,
        success=success,
        context=context or {},
    )
    _records.appendleft(rec)
    if success:
        _success_streak[agent_id] = _success_streak.get(agent_id, 0) + 1
    else:
        _success_streak[agent_id] = 0
        _apply_rules(rec)
    return rec


def _apply_rules(rec: FeedbackRecord) -> None:
    """Somut kurallar — düz metin özeti değil."""
    if rec.error_type != "rate_limit":
        return
    key = f"{rec.agent_id}:{rec.pipeline}"
    hits = sum(
        1
        for r in _records
        if r.agent_id == rec.agent_id
        and r.pipeline == rec.pipeline
        and r.error_type == "rate_limit"
        and time.time() - r.timestamp < RATE_LIMIT_SKIP_SECONDS
    )
    if hits >= RATE_LIMIT_HIT_THRESHOLD:
        _skip_until[key] = time.time() + RATE_LIMIT_SKIP_SECONDS


def should_skip_pipeline(agent_id: str, pipeline: str) -> Tuple[bool, str]:
    key = f"{agent_id}:{pipeline}"
    until = _skip_until.get(key, 0)
    if until > time.time():
        return True, f"skip_rule: rate_limit x{RATE_LIMIT_HIT_THRESHOLD} until {int(until - time.time())}s"
    return False, "ok"


def get_coordinator_actions() -> List[Dict[str, Any]]:
    """Koordinatör için yapılandırılmış aksiyon listesi."""
    actions: List[Dict[str, Any]] = []
    now = time.time()
    for key, until in _skip_until.items():
        if until > now:
            agent_id, pipeline = key.split(":", 1)
            actions.append(
                {
                    "action": "skip_pipeline",
                    "agent_id": agent_id,
                    "pipeline": pipeline,
                    "reason": "rate_limit_rule",
                    "retry_after_sec": int(until - now),
                }
            )
    recent_fails = [r for r in list(_records)[:10] if not r.success]
    for rec in recent_fails:
        actions.append(
            {
                "action": "avoid_repeat",
                "agent_id": rec.agent_id,
                "pipeline": rec.pipeline,
                "error_type": rec.error_type,
                "reason": rec.reason[:120],
            }
        )
    return actions


def record_pipeline_feedback(
    *,
    agent_ids: List[str],
    pipeline: str,
    success: bool,
    error: str = "",
    detail: Optional[Dict[str, Any]] = None,
) -> None:
    primary = agent_ids[0] if agent_ids else "oam.orchestrator.pipeline.local"
    http_status = (detail or {}).get("http_status")
    record_feedback(
        agent_id=primary,
        pipeline=pipeline,
        success=success,
        error=error or ("" if success else f"{pipeline} failed"),
        input_summary=str((detail or {}).get("input", ""))[:200],
        http_status=http_status,
        context={"agents": agent_ids, **(detail or {})},
    )


def get_feedback_status() -> Dict[str, Any]:
    return {
        "records": [r.to_public() for r in list(_records)[:20]],
        "coordinator_actions": get_coordinator_actions(),
        "success_streaks": dict(_success_streak),
        "skip_rules_active": len([u for u in _skip_until.values() if u > time.time()]),
        "total_records": len(_records),
    }


def reset_feedback() -> None:
    _records.clear()
    _success_streak.clear()
    _skip_until.clear()


# Backward compat
def get_brain_feedback() -> Dict[str, Any]:
    status = get_feedback_status()
    status["structured"] = True
    return status


def summarize_for_brain() -> str:
    actions = get_coordinator_actions()
    if not actions:
        return "no_actions"
    return str(actions[:3])
