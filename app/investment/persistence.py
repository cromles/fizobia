from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from app.investment.schemas import RevenueEvent, RevenueSource

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORE = ROOT / "data" / "hub_revenue.jsonl"


def is_demo_event(event: RevenueEvent) -> bool:
    return event.task_id.startswith("demo_")


def is_real_event(event: RevenueEvent) -> bool:
    if is_demo_event(event):
        return False
    if event.source in (RevenueSource.X402, RevenueSource.EXTERNAL):
        return True
    return event.source == RevenueSource.MESH_TASK and not event.task_id.startswith("sim_")


def load_revenue_events(store_path: Path) -> List[RevenueEvent]:
    if not store_path.exists():
        return []
    events: List[RevenueEvent] = []
    for line in store_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            raw = json.loads(line)
            if raw.get("created_at"):
                ts = str(raw["created_at"]).replace("Z", "")
                if "+" in ts:
                    ts = ts.split("+")[0]
                raw["created_at"] = datetime.fromisoformat(ts)
            events.append(RevenueEvent(**raw))
        except Exception:
            continue
    return events


def append_revenue_event(store_path: Path, event: RevenueEvent) -> None:
    store_path.parent.mkdir(parents=True, exist_ok=True)
    payload = event.model_dump(mode="json")
    with store_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, default=str) + "\n")


def rebuild_agent_totals(events: List[RevenueEvent]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for event in events:
        totals[event.agent_id] = totals.get(event.agent_id, 0.0) + event.gross_usd
    return totals


def rebuild_platform_total(events: List[RevenueEvent]) -> float:
    return sum(e.platform_usd for e in events)
