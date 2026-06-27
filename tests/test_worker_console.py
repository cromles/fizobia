"""İşçi kataloğu ve canlı veri uçları."""

from fastapi.testclient import TestClient

from app.api.main import app
from app.workers.web_crawler import AGENT_ID as WEB_ID


def test_hub_workers_catalog():
    client = TestClient(app)
    res = client.get("/hub/workers")
    assert res.status_code == 200
    body = res.json()
    assert body["count"] == 11
    assert body["expert_count"] == 4
    assert body["default_agent_id"] == WEB_ID
    ids = {w["agent_id"] for w in body["workers"]}
    assert WEB_ID in ids
    web = next(w for w in body["workers"] if w["agent_id"] == WEB_ID)
    assert web["token_symbol"] == "WEB-TKN"
    assert web["fixed_supply"] == 1_000_000
    assert web["live_route"] == "/hub/data/web"


def test_hub_data_web_feed():
    client = TestClient(app)
    res = client.get("/hub/data/web?limit=3")
    assert res.status_code == 200
    body = res.json()
    assert body.get("real_data") is True
    assert len(body.get("items", [])) >= 1
