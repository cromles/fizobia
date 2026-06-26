"""Gladyatör arenası ve mikro cüzdan testleri."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.mesh.agent_dialogue import reset_dialogue_bus
from app.mesh.agent_wallets import credit_agent, get_wallet, record_loss, reset_wallets
from app.mesh.arena_pipeline import run_arena_pipeline
from app.mesh.critic import anonymize_submissions, blind_audit
from app.mesh.hierarchy import reset_hierarchy_state
from app.mesh.mission import reset_mission_state
from app.mesh.organism import is_agent_eligible, record_pipeline_outcome, reset_organism_state
from app.mesh.purge import run_daily_purge
from app.workers.text_competitors import ARENA_TEXT_COMPETITORS, draft_for_agent


def _reset():
    reset_dialogue_bus()
    reset_hierarchy_state()
    reset_mission_state()
    reset_organism_state()
    reset_wallets()


@pytest.mark.asyncio
async def test_arena_pipeline_parallel_competition():
    _reset()
    result = await run_arena_pipeline(
        user_prompt=(
            "Son teknoloji haberleriyle ilgili 30 saniyelik dikey Instagram Reels üret."
        ),
    )
    assert result["job_id"].startswith("arena_")
    assert len(result["arena"]["drafts"]) == len(ARENA_TEXT_COMPETITORS)
    assert result["winner"]["agent_id"]
    assert result["render"]["format"] == "instagram_reels"
    assert result["arena"]["audit"]["blind"] is True


def test_blind_critic_picks_winner():
    drafts = [draft_for_agent(aid, user_prompt="tech reels hook") for aid in ARENA_TEXT_COMPETITORS]
    blind = anonymize_submissions(drafts)
    audit = blind_audit(blind)
    assert audit["winner_submission_id"]
    assert audit["reviews"][0]["critic_score"] >= audit["reviews"][-1]["critic_score"]
    for d in drafts:
        assert d["word_count"] >= 35


def test_critic_rejects_too_short_reels():
    blind = anonymize_submissions(
        [
            {
                "agent_id": "x",
                "draft": "Kalbim eskiden bir harabe",
                "word_count": 4,
                "target_format": "instagram_reels_vertical_30s",
            }
        ]
    )
    audit = blind_audit(blind)
    assert audit["reviews"][0]["verdict"] == "reject"
    assert audit["reviews"][0]["critic_score"] < 0.35


def test_micro_wallet_credit():
    _reset()
    credit_agent("oam.text.hook.local", 0.01, reason="test", job_id="job1")
    w = get_wallet("oam.text.hook.local")
    assert w.balance_usdc == 0.01
    assert w.tasks_won == 1


def test_purge_eliminates_low_success_agent():
    _reset()
    agent_id = ARENA_TEXT_COMPETITORS[0]
    for i in range(6):
        record_loss(agent_id, job_id=f"loss_{i}")
    out = run_daily_purge(force=True)
    assert agent_id in out["purged"] or not is_agent_eligible(agent_id)


def test_hub_prompt_endpoint_demo():
    _reset()
    client = TestClient(app)
    proof = '{"amount_usdc":0.10,"payer":"0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","payment_id":"test_arena"}'
    res = client.post(
        "/hub/prompt",
        json={
            "prompt": "Son teknoloji haberleriyle 30 saniyelik dikey Instagram Reels üret.",
            "background_music": True,
            "duration_sec": 30,
        },
        headers={"X-Payment-Proof": proof},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["result"]["winner"]["agent_id"]
    assert "revenue" in body


def test_hub_prompt_discover():
    client = TestClient(app)
    res = client.get("/hub/prompt")
    assert res.status_code == 200
    assert res.json()["service"] == "synapse-arena"


def test_hub_leaderboard_endpoint():
    client = TestClient(app)
    res = client.get("/hub/leaderboard")
    assert res.status_code == 200
    body = res.json()
    assert "agents" in body
    assert "total_tvl_usd" in body


@pytest.mark.asyncio
async def test_arena_returns_synapse_log():
    _reset()
    result = await run_arena_pipeline(
        user_prompt="Teknoloji haberleri için 30 saniyelik dikey Reels metni üret.",
    )
    assert len(result.get("synapse_log", [])) >= 3
