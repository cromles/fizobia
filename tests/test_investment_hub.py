import math

import pytest

from app.investment.bonding_curve import BondingCurve
from app.investment.hub import InvestmentHub
from app.investment.schemas import (
    AgentClass,
    AgentInvestmentProfile,
    BondingCurveParams,
    RevenueSplitConfig,
)
from app.protocol.schemas import AgentCapability, AgentManifest


def test_revenue_split_must_total_100():
    with pytest.raises(ValueError):
        RevenueSplitConfig(staking_share=0.65, platform_share=0.10, operator_share=0.20).validate_total()


def test_revenue_split_default():
    split = RevenueSplitConfig()
    split.validate_total()
    assert split.staking_share == 0.65
    assert split.platform_share == 0.10
    assert split.operator_share == 0.25


def test_bonding_curve_price_increases_with_supply():
    curve = BondingCurve(BondingCurveParams(base_price=0.01, slope=0.00001))
    p1 = curve.price_at_supply(0)
    p2 = curve.price_at_supply(1000)
    assert p2 > p1


def test_bonding_curve_mint_and_burn_roundtrip():
    curve = BondingCurve()
    shares, _ = curve.mint_shares(0, 100.0)
    assert shares > 0
    value = curve.burn_value(shares, shares)
    assert math.isclose(value, 100.0, rel_tol=0.01)


def _fetcher_manifest() -> AgentManifest:
    return AgentManifest(
        agent_id="test.fetcher",
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


def test_hub_stake_and_rewards():
    hub = InvestmentHub()
    hub.register_profile(
        AgentInvestmentProfile(
            agent_id="test.fetcher",
            display_name="Test Fetcher",
            agent_class=AgentClass.FETCHER,
            mission="test",
            token_symbol="TST-TKN",
        )
    )
    position = hub.pools.stake("0xinvestor1", "test.fetcher", 500.0)
    assert position.shares > 0
    assert position.staked_usdc == 500.0

    hub.record_execution(_fetcher_manifest(), "task_1", success=True, latency_ms=120.0)
    pending = hub.pools.get_position("0xinvestor1", "test.fetcher")
    assert pending is not None
    assert pending.rewards_pending_usdc > 0

    claimed = hub.pools.claim_rewards("0xinvestor1", "test.fetcher")
    assert claimed > 0


def test_hub_revenue_summary_endpoint():
    from fastapi.testclient import TestClient

    from app.api.main import app, router_mesh
    from app.registry.agent_registry import InMemoryAgentRegistry
    from app.workers.web_crawler import AGENT_ID as WEB_ID

    router_mesh.registry = InMemoryAgentRegistry()
    client = TestClient(app)

    manifest = AgentManifest(
        agent_id=WEB_ID,
        endpoint="http://127.0.0.1:9001",
        cost_per_token=1.0,
        capabilities=[
            AgentCapability(
                name="web_crawler",
                description="web veri çeker",
                input_schema={"type": "object", "properties": {}},
                output_schema={"type": "object", "properties": {}},
            )
        ],
    )
    client.post("/agents/register", json={"manifest": manifest.model_dump()})

    response = client.get("/hub/revenue/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["revenue_core_count"] == 7
    assert body["stake_mode"] in ("ledger_demo", "onchain")
    assert "totals" in body
    assert "agents" in body
    assert body["split"]["staking_share"] == 0.65


def test_hub_identity_card():
    hub = InvestmentHub()
    manifest = _fetcher_manifest()
    hub.ensure_agent(manifest)
    card = hub.build_identity_card("test.fetcher")
    assert card is not None
    assert card.profile.token_symbol.endswith("-TKN")
    assert card.pool.total_supply >= 0


def test_hub_api_endpoints():
    from fastapi.testclient import TestClient

    from app.api.main import app, router_mesh
    from app.registry.agent_registry import InMemoryAgentRegistry
    from app.workers.web_crawler import AGENT_ID as WEB_ID

    router_mesh.registry = InMemoryAgentRegistry()
    client = TestClient(app)

    manifest = AgentManifest(
        agent_id=WEB_ID,
        endpoint="http://127.0.0.1:9001",
        cost_per_token=1.0,
        capabilities=[
            AgentCapability(
                name="web_crawler",
                description="web veri çeker",
                input_schema={"type": "object", "properties": {}},
                output_schema={"type": "object", "properties": {}},
            )
        ],
    )
    client.post("/agents/register", json={"manifest": manifest.model_dump()})

    response = client.get("/hub/agents")
    assert response.status_code == 200
    agents = response.json()
    assert any(a["profile"]["agent_id"] == WEB_ID for a in agents)

    config = client.get("/hub/revenue/config")
    assert config.json()["staking_share"] == 0.65

    stake = client.post(
        "/hub/stake",
        json={"investor_id": "0xabc", "agent_id": WEB_ID, "amount_usdc": 100},
    )
    assert stake.status_code == 200
    assert stake.json()["shares"] > 0

    html = client.get("/hub")
    assert html.status_code == 200
    assert "Gelir döngüsü" in html.text or "kazan" in html.text
    assert "mesh-canvas" in html.text
    assert "worker-card" in html.text

    live = client.get("/hub/live")
    assert live.status_code == 200
    body = live.json()
    assert "network" in body
    assert "demo_mode" in body


def test_hub_live_integration_trigger():
    """Gerçek modda mesh görevi → gelir kaydı → /hub/live akışı."""
    import os

    os.environ["OAM_HUB_DEMO"] = "false"
    from fastapi.testclient import TestClient

    import app.investment.factory as hub_factory
    from app.agents.builtins import FETCHER_MANIFEST, SYNTHESIZER_MANIFEST, TRANSFORMER_MANIFEST
    from app.api.main import app, router_mesh
    from app.registry.agent_registry import InMemoryAgentRegistry

    hub_factory._hub = None
    router_mesh.registry = InMemoryAgentRegistry()
    for manifest in (FETCHER_MANIFEST, SYNTHESIZER_MANIFEST, TRANSFORMER_MANIFEST):
        router_mesh.upsert_agent(manifest)

    client = TestClient(app)
    version = client.get("/hub/version").json()
    assert version["demo_mode"] is False

    trigger = client.post("/hub/trigger-run")
    assert trigger.status_code == 200
    assert trigger.json()["tasks"] >= 1

    live = client.get("/hub/live").json()
    assert live["network"]["real_event_count"] >= 1
    assert all(not e.get("simulated") for e in live["activity_feed"])
