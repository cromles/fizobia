from datetime import datetime, timedelta, timezone

from app.investment.live import _tasks_per_minute
from app.investment.revenue import RevenueLedger
from app.investment.schemas import RevenueSplitConfig


def test_tasks_per_minute_from_recent_events():
    ledger = RevenueLedger(RevenueSplitConfig())
    now = datetime.now(timezone.utc)
    for i in range(6):
        ledger._events.append(
            type(
                "E",
                (),
                {
                    "created_at": now - timedelta(minutes=i * 5),
                },
            )()
        )
    rate = _tasks_per_minute(ledger._events, window_seconds=3600)
    assert rate > 0


def test_tasks_per_minute_empty():
    assert _tasks_per_minute([]) == 0.0
