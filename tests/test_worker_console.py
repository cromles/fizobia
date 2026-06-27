"""İşçi kataloğu — 10 hücre sinaps ağı."""

from fastapi.testclient import TestClient

from app.api.main import app
from app.mesh.cellular_taxonomy import CELLULAR_AGENT_IDS
from app.workers.web_crawler import AGENT_ID as WEB_ID


def test_hub_workers_catalog():
    client = TestClient(app)
    res = client.get("/hub/workers")
    assert res.status_code == 200
    body = res.json()
    assert body["count"] == 10
    assert body["topology"] == "dag"
    assert len(body.get("mesh_edges", [])) > 0
    ids = {w["agent_id"] for w in body["workers"]}
    assert ids == set(CELLULAR_AGENT_IDS)
    web = next(w for w in body["workers"] if w["agent_id"] == WEB_ID)
    assert web["cell_type"] == "sensory"
    assert web["live_route"] == "/hub/data/web"


def test_hub_data_web_feed():
    client = TestClient(app)
    res = client.get("/hub/data/web?limit=3")
    assert res.status_code == 200
    body = res.json()
    assert body.get("real_data") is True
    assert len(body.get("items", [])) >= 1
