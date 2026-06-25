from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.workers.market_pulse import fetch_market_snapshot, normalize_symbol

_MOCK_COINGECKO = {
    "bitcoin": {
        "usd": 97500.12,
        "usd_24h_change": 2.45,
        "usd_24h_vol": 28000000000,
        "usd_market_cap": 1900000000000,
    }
}


def test_normalize_symbol_aliases():
    assert normalize_symbol("BTC") == "bitcoin"
    assert normalize_symbol("eth") == "ethereum"


@patch("app.workers.market_pulse.httpx.Client")
def test_fetch_market_snapshot_real_shape(mock_client_cls):
    mock_response = MagicMock()
    mock_response.json.return_value = _MOCK_COINGECKO
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.get.return_value = mock_response
    mock_client_cls.return_value = mock_client

    result = fetch_market_snapshot("btc")
    assert result["real_data"] is True
    assert result["source"] == "coingecko"
    assert result["symbol"] == "bitcoin"
    assert result["price_usd"] == 97500.12
    assert "range_bound" in result["signals"]


def test_x402_market_pulse_flow():
    import app.investment.factory as hub_factory
    from app.agents.extended_builtins import MARKET_ANALYST
    from app.api.main import app, router_mesh
    from app.registry.agent_registry import InMemoryAgentRegistry

    hub_factory._hub = None
    router_mesh.registry = InMemoryAgentRegistry()
    router_mesh.upsert_agent(MARKET_ANALYST)

    client = TestClient(app)

    discover = client.get("/hub/x402/market-pulse?symbol=bitcoin")
    assert discover.status_code == 200
    assert discover.json()["real_data"] is True

    unpaid = client.post("/hub/x402/market-pulse/analyze", json={"symbol": "bitcoin"})
    assert unpaid.status_code == 402
    assert unpaid.json()["x402Version"] == 1

    proof = json.dumps(
        {
            "amount_usdc": 0.05,
            "payer": "0x" + "b" * 40,
            "payment_id": "test_pay_1",
        }
    )

    with patch(
        "app.api.hub_routes.fetch_market_snapshot_async",
        return_value={
            "agent_id": "oam.analyst.market.local",
            "symbol": "bitcoin",
            "price_usd": 100.0,
            "real_data": True,
            "source": "coingecko",
            "analysis": "BTC test",
            "signals": ["range_bound"],
            "confidence": 0.8,
        },
    ):
        paid = client.post(
            "/hub/x402/market-pulse/analyze",
            json={"symbol": "bitcoin"},
            headers={"X-Payment-Proof": proof},
        )

    assert paid.status_code == 200
    body = paid.json()
    assert body["paid"] is True
    assert body["revenue"]["staking_usd"] == pytest.approx(0.0325, rel=0.01)
    assert body["analysis"]["real_data"] is True

    live = client.get("/hub/live").json()
    x402_events = [e for e in live["activity_feed"] if "x402" in (e.get("source") or "")]
    assert len(x402_events) >= 1
