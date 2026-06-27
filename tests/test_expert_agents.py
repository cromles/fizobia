"""4 uzman işçi — katalog ve canlı veri uçları."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.api.main import app
from app.mesh.agent_catalog import EXPERT_AGENT_IDS
from app.workers.macro_strategist import AGENT_ID as MACRO_ID
from app.workers.regulatory_radar import AGENT_ID as REG_ID
from app.workers.threat_intel import AGENT_ID as THREAT_ID
from app.workers.yield_strategist import AGENT_ID as YIELD_ID


def test_hub_workers_includes_experts():
    client = TestClient(app)
    res = client.get("/hub/workers")
    assert res.status_code == 200
    body = res.json()
    assert body["count"] == 11
    assert body["expert_count"] == 4
    ids = {w["agent_id"] for w in body["workers"]}
    assert ids >= set(EXPERT_AGENT_IDS)
    macro = next(w for w in body["workers"] if w["agent_id"] == MACRO_ID)
    assert macro["tier"] == "expert"
    assert macro["token_symbol"] == "MAC-TKN"
    assert macro["live_route"] == "/hub/data/macro"


@patch(
    "app.workers.macro_strategist.fetch_macro_snapshot_async",
    new_callable=AsyncMock,
)
def test_hub_data_macro(mock_fetch):
    mock_fetch.return_value = {
        "agent_id": MACRO_ID,
        "btc_dominance_pct": 55.0,
        "real_data": True,
        "analysis": "test",
    }
    client = TestClient(app)
    res = client.get("/hub/data/macro")
    assert res.status_code == 200
    assert res.json()["real_data"] is True


@patch(
    "app.workers.regulatory_radar.fetch_regulatory_feed_async",
    new_callable=AsyncMock,
)
def test_hub_data_regulatory(mock_fetch):
    mock_fetch.return_value = {
        "agent_id": REG_ID,
        "items": [{"title": "SEC rule", "link": "https://x", "snippet": "policy"}],
        "count": 1,
        "real_data": True,
    }
    client = TestClient(app)
    res = client.get("/hub/data/regulatory")
    assert res.status_code == 200
    assert len(res.json()["items"]) == 1


@patch(
    "app.workers.threat_intel.fetch_threat_snapshot_async",
    new_callable=AsyncMock,
)
def test_hub_data_threat(mock_fetch):
    mock_fetch.return_value = {
        "agent_id": THREAT_ID,
        "items": [{"cve": "CVE-2024-0001", "vendor": "Acme", "product": "X"}],
        "count": 1,
        "real_data": True,
    }
    client = TestClient(app)
    res = client.get("/hub/data/threat")
    assert res.status_code == 200
    assert res.json()["items"][0]["cve"] == "CVE-2024-0001"


@patch(
    "app.workers.yield_strategist.fetch_yield_snapshot_async",
    new_callable=AsyncMock,
)
def test_hub_data_yield(mock_fetch):
    mock_fetch.return_value = {
        "agent_id": YIELD_ID,
        "items": [{"project": "aave", "symbol": "USDC", "apy_pct": 4.2, "tvl_usd": 1e8}],
        "count": 1,
        "real_data": True,
    }
    client = TestClient(app)
    res = client.get("/hub/data/yield")
    assert res.status_code == 200
    assert res.json()["items"][0]["project"] == "aave"
