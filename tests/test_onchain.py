"""On-chain staking doğrulama testleri."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.investment.onchain import build_public_config, get_deployment, usdc_to_wei, wei_to_usdc


def test_usdc_wei_conversion():
    assert usdc_to_wei(1.0) == 1_000_000
    assert wei_to_usdc(1_000_000) == 1.0


def test_build_public_config_off_by_default(monkeypatch):
    monkeypatch.setenv("OAM_ONCHAIN_ENABLED", "false")
    from app.config import OAMSettings

    cfg = OAMSettings.from_env()
    assert cfg.onchain_enabled is False


def test_deployment_file_loads():
    import app.investment.onchain as onchain_mod

    onchain_mod._deployment = None
    path = Path(__file__).resolve().parents[1] / "deployments" / "local.json"
    if not path.exists():
        pytest.skip("deployments/local.json yok")
    data = json.loads(path.read_text())
    deployment = get_deployment()
    assert deployment is not None
    assert deployment.usdc.startswith("0x")
    assert "oam.fetcher.local" in deployment.pools


def test_hub_onchain_config_endpoint():
    from fastapi.testclient import TestClient

    from app.api.main import app

    client = TestClient(app)
    response = client.get("/hub/onchain/config")
    assert response.status_code == 200
    body = response.json()
    assert "enabled" in body
    assert "chain_id" in body


def test_hub_sdk_config_endpoint():
    from fastapi.testclient import TestClient

    from app.api.main import app

    client = TestClient(app)
    response = client.get("/hub/sdk/config")
    assert response.status_code == 200
    body = response.json()
    assert body["protocol"] == "OAM-Hub-SDK"
    assert "embed_url" in body
    assert "endpoints" in body
    assert "agents" in body["endpoints"]


def test_hub_embed_page():
    from fastapi.testclient import TestClient

    from app.api.main import app

    client = TestClient(app)
    response = client.get("/hub/embed")
    assert response.status_code == 200
    assert "Zinesh Protocol" in response.text
    assert "frame-ancestors" in response.headers.get("content-security-policy", "")
