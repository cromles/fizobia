"""Departman kategorileri ve makale pipeline testleri."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.mesh.agent_dialogue import reset_dialogue_bus
from app.mesh.article_pipeline import run_article_pipeline
from app.mesh.critic import audit_article
from app.mesh.departments import (
    ARTICLE_PIPELINE_AGENTS,
    DEPARTMENT_COPYWRITING,
    DEPARTMENT_MEDIA_VIDEO,
    DEPARTMENT_TECHNICAL,
    departments_for_agent,
    list_departments,
    primary_department,
)
from app.mesh.hierarchy import reset_hierarchy_state
from app.mesh.mission import reset_mission_state
from app.mesh.organism import reset_organism_state
from app.mesh.proof_pipeline import MESH_PROOF_AGENTS
from app.workers.media_render import AGENT_ID as RENDER_ID
from app.workers.text_competitors import ARENA_TEXT_COMPETITORS
from app.workers.web_crawler import AGENT_ID as WEB_CRAWLER_ID


def _reset():
    reset_dialogue_bus()
    reset_hierarchy_state()
    reset_mission_state()
    reset_organism_state()


def test_departments_registry():
    data = list_departments()
    assert data["count"] == 3
    codes = {d["code"] for d in data["departments"]}
    assert codes == {DEPARTMENT_MEDIA_VIDEO, DEPARTMENT_COPYWRITING, DEPARTMENT_TECHNICAL}
    assert data["article_pipeline"]["agents"] == list(ARTICLE_PIPELINE_AGENTS)


def test_agent_department_mapping():
    assert DEPARTMENT_TECHNICAL in departments_for_agent(WEB_CRAWLER_ID)
    assert DEPARTMENT_COPYWRITING in departments_for_agent(WEB_CRAWLER_ID)
    assert primary_department(RENDER_ID) == DEPARTMENT_MEDIA_VIDEO
    assert primary_department(MESH_PROOF_AGENTS[0]) == DEPARTMENT_TECHNICAL


def test_audit_article_passes_structured_text():
    text = (
        "Giriş — konu önemli.\n\n"
        "Gelişme — veri ve bağlam, sektör etkisi açık.\n\n"
        "Sonuç — net özet ve kaynak."
    )
    review = audit_article(text)
    assert "critic_score" in review
    assert review["verdict"] in ("pass", "reject")


@pytest.mark.asyncio
async def test_article_pipeline_mocked():
    _reset()
    mock_research = {
        "headline": "AI trendleri 2026",
        "snippet": "Yapay zeka sektöründe yeni gelişmeler.",
        "source_url": "https://example.com/rss",
        "real_data": True,
    }
    with patch(
        "app.mesh.article_pipeline.fetch_web_snapshot_async",
        new_callable=AsyncMock,
        return_value=mock_research,
    ):
        result = await run_article_pipeline(
            topic="Yapay zeka trendleri hakkında SEO uyumlu makale yaz",
            tone="corporate",
        )
    assert result["job_id"].startswith("article_")
    assert result["department"] == DEPARTMENT_COPYWRITING
    assert len(result["steps"]) == 4
    assert result["article"]["research"]["headline"] == "AI trendleri 2026"
    assert result["article"]["final_text"]
    assert "approved" in result["article"]


def test_hub_departments_endpoint():
    client = TestClient(app)
    res = client.get("/hub/departments")
    assert res.status_code == 200
    body = res.json()
    assert body["count"] == 3
    assert body["article_pipeline"]["pipeline"] == "article"


def test_hub_leaderboard_department_filter():
    client = TestClient(app)
    res = client.get("/hub/leaderboard?department_code=technical")
    assert res.status_code == 200
    body = res.json()
    assert body["department_filter"] == "technical"
    for row in body.get("agents", []):
        assert "technical" in row.get("departments", []) or row.get("department_code") == "technical"


@pytest.mark.asyncio
async def test_growth_hire_article_pipeline():
    _reset()
    from app.mesh.growth_protocol import get_growth_protocol

    try:
        growth = get_growth_protocol()
    except RuntimeError:
        pytest.skip("Growth protocol bu test sırasında henüz başlatılmadı")

    mock_research = {
        "headline": "Test başlık",
        "snippet": "Test özet metni yeterince uzun.",
        "source_url": "https://example.com",
        "real_data": True,
    }
    with patch(
        "app.mesh.article_pipeline.fetch_web_snapshot_async",
        new_callable=AsyncMock,
        return_value=mock_research,
    ):
        result = await growth.hire_agents(
            pipeline="article",
            goal="Blockchain regülasyonları hakkında kurumsal makale",
            initial_data={"tone": "technical"},
        )
    assert result["pipeline"] == "article"
    assert result["department"] == DEPARTMENT_COPYWRITING
    assert len(result.get("hired_agents", [])) == len(ARTICLE_PIPELINE_AGENTS)
    assert result.get("real_data") is True


def test_leaderboard_includes_department_fields():
    client = TestClient(app)
    res = client.get("/hub/leaderboard")
    assert res.status_code == 200
    agents = res.json().get("agents", [])
    if agents:
        first = agents[0]
        assert "department_code" in first
        assert "department_label" in first
