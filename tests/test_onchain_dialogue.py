"""On-Chain-Watcher ve ajan diyaloğu testleri."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.mesh.agent_dialogue import get_dialogue_bus, reset_dialogue_bus
from app.mesh.proof_pipeline import run_mesh_proof_pipeline
from app.workers.on_chain_watcher import fetch_chain_snapshot


def test_chain_snapshot_mocked_rpc():
    with patch("app.workers.on_chain_watcher._rpc") as mock_rpc:
        mock_rpc.side_effect = ["0x64", "0x14a34"]
        snap = fetch_chain_snapshot(symbol="bitcoin")
    assert snap["real_data"] is True
    assert snap["block_number"] == 100
    assert snap["chain_id"] == 84532


@pytest.mark.asyncio
async def test_mesh_proof_includes_dialogue_and_onchain():
    reset_dialogue_bus()
    web = {"headline": "BTC rally", "snippet": "ETF inflows", "real_data": True}
    sentiment = {"sentiment": "bullish", "fear_greed_index": 70, "real_data": True}
    market = {"symbol": "bitcoin", "price_usd": 98000.0, "change_24h_pct": 2.5, "real_data": True}
    chain = {
        "network": "base-sepolia",
        "block_number": 12345,
        "real_data": True,
        "analysis": "chain ok",
    }
    with (
        patch("app.mesh.proof_pipeline.fetch_web_snapshot_async", AsyncMock(return_value=web)),
        patch("app.mesh.proof_pipeline.fetch_sentiment_snapshot_async", AsyncMock(return_value=sentiment)),
        patch("app.mesh.proof_pipeline.fetch_market_snapshot_async", AsyncMock(return_value=market)),
        patch("app.mesh.proof_pipeline.fetch_chain_snapshot_async", AsyncMock(return_value=chain)),
    ):
        result = await run_mesh_proof_pipeline(symbol="bitcoin")

    assert result["workers_used"] == 4
    assert len(result["steps"]) == 4
    assert result["dialogue_messages"] >= 5
    bus = get_dialogue_bus()
    thread = bus.thread_summary(result["dialogue_thread"])
    assert len(thread["participants"]) >= 3


def test_dialogue_api_roundtrip():
    reset_dialogue_bus()
    client = TestClient(app)
    sent = client.post(
        "/hub/ecosystem/dialogue",
        json={
            "from_agent": "oam.orchestrator.pipeline.local",
            "to_agent": "oam.fetcher.web.local",
            "text": "Tarama başlat",
            "intent": "hire_request",
        },
    )
    assert sent.status_code == 200
    body = sent.json()
    assert body["from"] == "oam.orchestrator.pipeline.local"

    listed = client.get("/hub/ecosystem/dialogue?limit=5").json()
    assert listed["count"] >= 1


def test_ecosystem_hire_includes_dialogue():
    reset_dialogue_bus()
    import app.investment.factory as hub_factory
    from app.agents.founder_bootstrap import bootstrap_full_agents
    from app.api.main import app, peer_discovery, router_mesh
    from app.registry.agent_registry import InMemoryAgentRegistry

    hub_factory._hub = None
    router_mesh.registry = InMemoryAgentRegistry()
    bootstrap_full_agents(router_mesh, peer_discovery)

    client = TestClient(app)
    with patch(
        "app.mesh.growth_protocol.run_mesh_proof_pipeline",
        AsyncMock(
            return_value={
                "proof_id": "proof_dialogue1",
                "verdict": "ok",
                "total_latency_ms": 100,
                "steps": [{}, {}, {}, {}],
                "dialogue_thread": "proof_abc",
                "dialogue_messages": 7,
                "real_data": True,
            }
        ),
    ):
        response = client.post("/hub/ecosystem/hire", json={"pipeline": "mesh_proof"})
    assert response.status_code == 200
    body = response.json()
    assert len(body.get("hired_agents", [])) == 4
    assert body.get("dialogue_thread") == "proof_abc"
