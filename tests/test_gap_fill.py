import os
import time

import pytest

from app.investment.hub import InvestmentHub
from app.investment.metrics import MetricsCollector, _RevenuePoint
from app.investment.schemas import AgentClass, AgentInvestmentProfile, PartnershipMode
from app.investment.x402 import parse_x402_payment, verify_webhook_secret
from app.protocol.schemas import AgentCapability, AgentManifest


def _manifest(agent_id: str = "test.fetcher") -> AgentManifest:
    return AgentManifest(
        agent_id=agent_id,
        endpoint="http://127.0.0.1:9001",
        cost_per_token=1.0,
        capabilities=[
            AgentCapability(
                name="data_fetcher",
                description="veri çeker",
                input_schema={"type": "object", "properties": {}},
                output_schema={"type": "object", "properties": {}},
            )
        ],
    )


def test_default_manifests_count_at_least_10():
    from app.agents.builtins import DEFAULT_MANIFESTS

    assert len(DEFAULT_MANIFESTS) >= 10


def test_parse_x402_payment():
    parsed = parse_x402_payment(
        {
            "agent_id": "oam.fetcher.local",
            "amount_usdc": 12.5,
            "payer": "0x" + "a" * 40,
            "tx_hash": "0x" + "b" * 64,
        }
    )
    assert parsed["amount_usdc"] == 12.5
    assert parsed["agent_id"] == "oam.fetcher.local"


def test_volume_24h_rolling_window():
    metrics = MetricsCollector()
    old_ts = time.time() - 90000
    metrics._agents["a1"].revenue_points = [
        _RevenuePoint(amount_usd=5.0, timestamp=old_ts),
        _RevenuePoint(amount_usd=3.0, timestamp=time.time()),
    ]
    assert metrics.volume_24h("a1") == pytest.approx(3.0)


def test_hub_external_revenue_distributes_staking():
    hub = InvestmentHub()
    hub.register_profile(
        AgentInvestmentProfile(
            agent_id="test.fetcher",
            display_name="Test",
            agent_class=AgentClass.FETCHER,
            mission="test",
            token_symbol="TST-TKN",
            partnership_mode=PartnershipMode.PASSIVE,
        )
    )
    hub.pools.stake("0xinv", "test.fetcher", 100.0)
    hub.record_external_revenue(_manifest(), "x402_job_1", 10.0, tx_hash="0x" + "c" * 64)
    pos = hub.pools.get_position("0xinv", "test.fetcher")
    assert pos is not None
    assert pos.rewards_pending_usdc == pytest.approx(6.5, rel=0.01)
    events = hub.revenue.list_events(agent_id="test.fetcher")
    assert events[-1].source.value == "x402"


def test_hub_api_x402_and_discovery():
    from fastapi.testclient import TestClient

    import app.investment.factory as hub_factory
    from app.agents.builtins import FETCHER_MANIFEST
    from app.api.main import app, router_mesh
    from app.registry.agent_registry import InMemoryAgentRegistry

    hub_factory._hub = None
    router_mesh.registry = InMemoryAgentRegistry()
    router_mesh.upsert_agent(FETCHER_MANIFEST)

    client = TestClient(app)

    discovery = client.get("/hub/discovery")
    assert discovery.status_code == 200
    body = discovery.json()
    assert body["agent_count"] >= 1
    assert "positioning" in body

    well_known = client.get("/.well-known/agent.json")
    assert well_known.status_code == 200
    assert "OAM Hub" in well_known.json()["name"]

    mpp = client.get("/.well-known/mpp.json")
    assert mpp.status_code == 200
    assert mpp.json()["protocol"] == "MPP"

    partnership = client.get("/hub/partnership/info")
    assert partnership.status_code == 200
    assert partnership.json()["mode"] == "passive_partnership"

    x402 = client.post(
        "/hub/revenue/x402",
        json={"agent_id": "oam.fetcher.local", "amount_usdc": 5.0},
    )
    assert x402.status_code == 200
    assert x402.json()["staking_usd"] == pytest.approx(3.25, rel=0.01)

    passive = client.post(
        "/hub/partnership/stake",
        json={
            "investor_id": "0xpartner",
            "agent_id": "oam.fetcher.local",
            "amount_usdc": 50,
        },
    )
    assert passive.status_code == 200
    assert passive.json()["partnership_mode"] == "passive"
    assert "message" in passive.json()


def test_webhook_secret_when_configured(monkeypatch):
    from types import SimpleNamespace

    from app.investment import x402 as x402_mod

    monkeypatch.setattr(
        x402_mod,
        "settings",
        SimpleNamespace(x402_webhook_secret="test-secret"),
    )
    assert x402_mod.verify_webhook_secret(None) is False

    import hashlib
    import hmac

    sig = hmac.new(b"test-secret", b"x402-hub", hashlib.sha256).hexdigest()
    assert x402_mod.verify_webhook_secret(sig) is True
