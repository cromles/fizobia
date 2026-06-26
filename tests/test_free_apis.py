"""Ücretsiz dış API işçileri ve hub uç noktaları."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.mesh.data_sources import FREE_DATA_SOURCES, list_data_sources
from app.workers.btc_network import fetch_btc_network_snapshot
from app.workers.defi_pulse import fetch_defi_snapshot
from app.workers.fx_pulse import fetch_fx_snapshot


def test_data_sources_catalog():
    catalog = list_data_sources()
    assert catalog["total"] >= 7
    assert catalog["free_no_auth"] >= 6
    ids = {s["id"] for s in FREE_DATA_SOURCES}
    assert "frankfurter" in ids
    assert "defillama" in ids
    assert "mempool_space" in ids


@patch("app.workers.fx_pulse.httpx.Client")
def test_fetch_fx_snapshot(mock_client_cls):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "amount": 1.0,
        "base": "USD",
        "date": "2026-06-25",
        "rates": {"TRY": 46.5, "EUR": 0.92},
    }
    mock_resp.raise_for_status = MagicMock()
    mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp

    result = fetch_fx_snapshot(base="USD", symbols="TRY,EUR")
    assert result["real_data"] is True
    assert result["usd_try"] == 46.5
    assert result["source"] == "frankfurter.dev"


@patch("app.workers.defi_pulse.httpx.Client")
def test_fetch_defi_snapshot(mock_client_cls):
    mock_resp = MagicMock()
    mock_resp.json.return_value = [
        {"name": "Ethereum", "tokenSymbol": "ETH", "tvl": 50_000_000_000},
        {"name": "BSC", "tokenSymbol": "BSC", "tvl": 5_000_000_000},
    ]
    mock_resp.raise_for_status = MagicMock()
    mock_client_cls.return_value.__enter__.return_value.get.return_value = mock_resp

    result = fetch_defi_snapshot(limit=2)
    assert result["real_data"] is True
    assert result["leader_chain"] == "Ethereum"
    assert len(result["top_chains"]) == 2


@patch("app.workers.btc_network.httpx.Client")
def test_fetch_btc_network_snapshot(mock_client_cls):
    mock_client = MagicMock()
    fees_resp = MagicMock()
    fees_resp.json.return_value = {"fastestFee": 12, "halfHourFee": 8, "hourFee": 6, "economyFee": 4, "minimumFee": 1}
    fees_resp.raise_for_status = MagicMock()
    height_resp = MagicMock()
    height_resp.text = "800000"
    height_resp.raise_for_status = MagicMock()
    ticker_resp = MagicMock()
    ticker_resp.json.return_value = {"USD": {"last": 59000.0}}
    ticker_resp.raise_for_status = MagicMock()
    mock_client.get.side_effect = [fees_resp, height_resp, ticker_resp]
    mock_client_cls.return_value.__enter__.return_value = mock_client

    result = fetch_btc_network_snapshot()
    assert result["real_data"] is True
    assert result["block_height"] == 800000
    assert result["btc_usd"] == 59000.0


def test_hub_apis_endpoint():
    client = TestClient(app)
    res = client.get("/hub/apis")
    assert res.status_code == 200
    body = res.json()
    assert body["free_no_auth"] >= 6
    assert "data_routes" in body


@pytest.mark.asyncio
async def test_hub_data_fx_route():
    client = TestClient(app)
    with patch(
        "app.workers.fx_pulse.fetch_fx_snapshot_async",
        new=AsyncMock(
            return_value={
                "agent_id": "oam.analyst.fx.local",
                "usd_try": 46.5,
                "real_data": True,
                "source": "frankfurter.app",
            }
        ),
    ):
        res = client.get("/hub/data/fx?symbols=TRY")
    assert res.status_code == 200
    assert res.json()["real_data"] is True
