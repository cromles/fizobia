"""10 hücre sinaps kataloğu — uzman hücreler dahil."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.api.main import app
from app.workers.macro_strategist import AGENT_ID as MACRO_ID
from app.workers.threat_intel import AGENT_ID as THREAT_ID
from app.workers.yield_strategist import AGENT_ID as YIELD_ID


def test_hub_workers_ten_cells():
    client = TestClient(app)
    res = client.get("/hub/workers")
    assert res.status_code == 200
    body = res.json()
    assert body["count"] == 10
    ids = {w["agent_id"] for w in body["workers"]}
    assert MACRO_ID in ids
    assert THREAT_ID in ids
    assert YIELD_ID in ids


@patch(
    "app.workers.macro_strategist.fetch_macro_snapshot_async",
    new_callable=AsyncMock,
)
def test_hub_data_macro(mock_fetch):
    mock_fetch.return_value = {"agent_id": MACRO_ID, "btc_dominance_pct": 55.0, "real_data": True}
    client = TestClient(app)
    res = client.get("/hub/data/macro")
    assert res.status_code == 200
    assert res.json()["real_data"] is True
