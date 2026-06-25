from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.mesh.proof_pipeline import run_mesh_proof_pipeline
from app.workers.web_crawler import _parse_rss, _strip_html

_SAMPLE_RSS = """<?xml version="1.0"?>
<rss><channel>
<item><title>Bitcoin hits new weekly high</title>
<link>https://example.com/btc</link>
<description><![CDATA[Markets rally on ETF inflows and risk-on sentiment]]></description>
</item>
</channel></rss>"""


def test_strip_html():
    assert "hello" in _strip_html("<p>hello <b>world</b></p>")


def test_parse_rss():
    parsed = _parse_rss(_SAMPLE_RSS)
    assert "Bitcoin" in parsed["title"]
    assert "ETF" in parsed["snippet"]


@pytest.mark.asyncio
async def test_mesh_proof_pipeline_mocked():
    web = {
        "headline": "Bitcoin hits new weekly high",
        "snippet": "Markets rally on ETF inflows",
        "real_data": True,
    }
    sentiment = {
        "sentiment": "bullish",
        "fear_greed_index": 68,
        "real_data": True,
        "analysis": "test",
    }
    market = {
        "symbol": "bitcoin",
        "price_usd": 97000.0,
        "change_24h_pct": 2.1,
        "real_data": True,
        "analysis": "BTC",
    }
    with (
        patch("app.mesh.proof_pipeline.fetch_web_snapshot_async", AsyncMock(return_value=web)),
        patch("app.mesh.proof_pipeline.fetch_sentiment_snapshot_async", AsyncMock(return_value=sentiment)),
        patch("app.mesh.proof_pipeline.fetch_market_snapshot_async", AsyncMock(return_value=market)),
    ):
        result = await run_mesh_proof_pipeline(symbol="bitcoin")
    assert result["real_data"] is True
    assert len(result["steps"]) == 3
    assert "Bitcoin" in result["verdict"]


def test_mesh_proof_x402_endpoint():
    import app.investment.factory as hub_factory
    from app.agents.extended_builtins import MARKET_ANALYST, SENTIMENT_ANALYST, WEB_FETCHER
    from app.api.main import app, router_mesh
    from app.registry.agent_registry import InMemoryAgentRegistry

    hub_factory._hub = None
    router_mesh.registry = InMemoryAgentRegistry()
    for manifest in (WEB_FETCHER, SENTIMENT_ANALYST, MARKET_ANALYST):
        router_mesh.upsert_agent(manifest)

    client = TestClient(app)
    discover = client.get("/hub/proof/mesh")
    assert discover.status_code == 200
    assert discover.json()["workers"] == [
        "Web-Crawler-Pro",
        "Sentiment-Radar",
        "Market-Pulse",
    ]

    unpaid = client.post("/hub/proof/mesh/run", json={"symbol": "bitcoin"})
    assert unpaid.status_code == 402

    proof = json.dumps(
        {
            "amount_usdc": 0.10,
            "payer": "0x" + "d" * 40,
            "payment_id": "mesh_test_1",
        }
    )
    pipeline_result = {
        "proof_id": "proof_test123",
        "real_data": True,
        "verdict": "test verdict",
        "steps": [],
        "message": "ok",
    }
    with patch(
        "app.api.hub_routes.run_mesh_proof_pipeline",
        AsyncMock(return_value=pipeline_result),
    ):
        paid = client.post(
            "/hub/proof/mesh/run",
            json={"symbol": "bitcoin"},
            headers={"X-Payment-Proof": proof},
        )
    assert paid.status_code == 200
    body = paid.json()
    assert body["paid"] is True
    assert len(body["revenue"]["splits"]) == 3
