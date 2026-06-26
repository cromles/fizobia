"""On-chain staking doğrulama testleri."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from eth_abi import encode as abi_encode
from eth_utils import keccak, to_checksum_address

from app.investment.onchain import (
    UNSTAKED_TOPIC,
    build_public_config,
    get_deployment,
    usdc_to_wei,
    verify_unstake_tx,
    wei_to_usdc,
)


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


def test_build_public_config_base_sepolia_metadata():
    import app.investment.onchain as onchain_mod

    prev = onchain_mod._deployment
    onchain_mod._deployment = onchain_mod.OnchainDeployment(
        chain_id=84532,
        network="base-sepolia",
        rpc_url="https://sepolia.base.org",
        deployer="0x" + "1" * 40,
        usdc="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        factory="0x" + "2" * 40,
        pools={},
        usdc_decimals=6,
    )
    try:
        cfg = build_public_config()
        assert cfg["chain_id"] == 84532
        assert cfg["chain_name"] == "Base Sepolia"
        assert cfg["stake_mode"] in ("ledger_demo", "onchain")
        assert "https://sepolia.base.org" in cfg["rpc_urls"]
        assert "https://sepolia.basescan.org" in cfg["block_explorer_urls"]
    finally:
        onchain_mod._deployment = prev


def _mock_unstake_receipt(pool: str, investor: str, shares_wei: int):
    investor = to_checksum_address(investor)
    data = abi_encode(["uint256", "uint256"], [shares_wei, shares_wei])
    return {
        "status": "0x1",
        "logs": [
            {
                "address": pool,
                "topics": [
                    UNSTAKED_TOPIC,
                    "0x" + "0" * 24 + investor[2:].lower(),
                ],
                "data": "0x" + data.hex(),
            }
        ],
    }


@patch("app.investment.onchain._wait_for_receipt")
def test_verify_unstake_tx_ok(mock_wait):
    import app.investment.onchain as onchain_mod

    pool = "0x" + "a" * 40
    investor = "0x" + "b" * 40
    agent_id = "oam.fetcher.web.local"
    shares = 50.0
    shares_wei = usdc_to_wei(shares)

    onchain_mod._deployment = onchain_mod.OnchainDeployment(
        chain_id=84532,
        network="base-sepolia",
        rpc_url="https://sepolia.base.org",
        deployer="0x" + "1" * 40,
        usdc="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        factory="0x" + "2" * 40,
        pools={agent_id: {"address": pool, "token_symbol": "WCP-TKN"}},
        usdc_decimals=6,
    )
    mock_wait.return_value = _mock_unstake_receipt(pool, investor, shares_wei)

    proof = verify_unstake_tx("0x" + "c" * 64, investor, agent_id, shares)
    assert proof["usdc_returned"] == shares
    assert proof["pool"] == pool


@patch("app.investment.onchain._wait_for_receipt")
def test_verify_unstake_tx_wrong_shares(mock_wait):
    import app.investment.onchain as onchain_mod

    pool = "0x" + "a" * 40
    investor = "0x" + "b" * 40
    agent_id = "oam.fetcher.web.local"

    onchain_mod._deployment = onchain_mod.OnchainDeployment(
        chain_id=84532,
        network="base-sepolia",
        rpc_url="https://sepolia.base.org",
        deployer="0x" + "1" * 40,
        usdc="0x036CbD53842c5426634e7929541eC2318f3dCF7e",
        factory="0x" + "2" * 40,
        pools={agent_id: {"address": pool, "token_symbol": "WCP-TKN"}},
        usdc_decimals=6,
    )
    mock_wait.return_value = _mock_unstake_receipt(pool, investor, usdc_to_wei(10.0))

    with pytest.raises(ValueError, match="uyuşmuyor"):
        verify_unstake_tx("0x" + "c" * 64, investor, agent_id, 50.0)
