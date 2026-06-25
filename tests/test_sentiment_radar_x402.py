from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.workers.sentiment_radar import fetch_sentiment_snapshot, score_text_sentiment

_MOCK_FNG = {
    "data": [
        {
            "value": "72",
            "value_classification": "Greed",
            "timestamp": "1719000000",
        }
    ]
}


def test_score_text_sentiment_bullish():
    label, score, tags = score_text_sentiment("Bitcoin rally surge record growth approval")
    assert label == "bullish"
    assert score > 0
    assert tags


@patch("app.workers.sentiment_radar.httpx.Client")
def test_fetch_sentiment_snapshot_shape(mock_client_cls):
    mock_response = MagicMock()
    mock_response.json.return_value = _MOCK_FNG
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.return_value = mock_response
    mock_client_cls.return_value = mock_client

    result = fetch_sentiment_snapshot("Fed rate cut boosts crypto optimism")
    assert result["real_data"] is True
    assert result["fear_greed_index"] == 72
    assert result["sentiment"] in {"bullish", "neutral", "bearish"}
    assert "analysis" in result


def test_x402_sentiment_radar_flow():
    import app.investment.factory as hub_factory
    from app.agents.extended_builtins import SENTIMENT_ANALYST
    from app.api.main import app, router_mesh
    from app.registry.agent_registry import InMemoryAgentRegistry

    hub_factory._hub = None
    router_mesh.registry = InMemoryAgentRegistry()
    router_mesh.upsert_agent(SENTIMENT_ANALYST)

    client = TestClient(app)

    discover = client.get("/hub/x402/sentiment-radar")
    assert discover.status_code == 200
    assert discover.json()["real_data"] is True
    assert len(client.get("/hub/x402/services").json()["services"]) >= 2

    unpaid = client.post(
        "/hub/x402/sentiment-radar/analyze",
        json={"text": "Bitcoin crash fear selloff"},
    )
    assert unpaid.status_code == 402

    proof = json.dumps(
        {
            "amount_usdc": 0.04,
            "payer": "0x" + "c" * 40,
            "payment_id": "test_sent_1",
        }
    )

    with patch(
        "app.api.hub_routes.fetch_sentiment_snapshot_async",
        return_value={
            "agent_id": "oam.analyst.sentiment.local",
            "sentiment": "bearish",
            "score": -0.4,
            "real_data": True,
            "source": "alternative.me+fng+lexicon",
            "analysis": "test sentiment",
            "fear_greed_index": 30,
        },
    ):
        paid = client.post(
            "/hub/x402/sentiment-radar/analyze",
            json={"text": "Bitcoin crash fear selloff"},
            headers={"X-Payment-Proof": proof},
        )

    assert paid.status_code == 200
    body = paid.json()
    assert body["paid"] is True
    assert body["revenue"]["staking_usd"] == pytest.approx(0.026, rel=0.01)
