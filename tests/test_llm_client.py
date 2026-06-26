"""LLM istemci testleri."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import AsyncMock, patch

import pytest

from app.config import settings
from app.llm.client import chat_completion, llm_public_status
from app.workers.text_competitors import AGENT_HOOK_ID, draft_for_agent_async


def _llm_settings():
    return replace(
        settings,
        llm_api_key="test-key",
        llm_base_url="https://api.example.com/v1",
        llm_model="test-model",
    )


def test_llm_status_without_key():
    status = llm_public_status()
    assert "enabled" in status
    assert "cheap_providers" in status


@pytest.mark.asyncio
async def test_arena_uses_template_without_key():
    with patch("app.config.settings", replace(settings, llm_api_key="")):
        result = await draft_for_agent_async(AGENT_HOOK_ID, user_prompt="AI trendleri reels metni")
    assert result["source"] == "template"
    assert result["draft"]


@pytest.mark.asyncio
async def test_arena_uses_llm_when_configured():
    mock_response = {
        "choices": [{"message": {"content": "Dur! Bu gerçek LLM metni."}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 8},
    }
    llm = _llm_settings()

    with patch("app.config.settings", llm), patch("app.llm.client.settings", llm):
        with patch("app.llm.client.httpx.AsyncClient") as mock_client:
            instance = mock_client.return_value.__aenter__.return_value
            instance.post = AsyncMock(
                return_value=type(
                    "R",
                    (),
                    {"raise_for_status": lambda self: None, "json": lambda self: mock_response},
                )()
            )
            result = await draft_for_agent_async(AGENT_HOOK_ID, user_prompt="AI trendleri reels")
    assert result["source"] == "llm"
    assert "LLM" in result["draft"] or "gerçek" in result["draft"]


@pytest.mark.asyncio
async def test_chat_completion_parses_response():
    mock_response = {
        "choices": [{"message": {"content": "Merhaba dünya"}}],
        "usage": {},
    }
    llm = _llm_settings()
    with patch("app.config.settings", llm), patch("app.llm.client.settings", llm):
        with patch("app.llm.client.httpx.AsyncClient") as mock_client:
            instance = mock_client.return_value.__aenter__.return_value
            instance.post = AsyncMock(
                return_value=type(
                    "R",
                    (),
                    {"raise_for_status": lambda self: None, "json": lambda self: mock_response},
                )()
            )
            text, meta = await chat_completion(system="test", user="hi")
    assert "Merhaba" in text
    assert meta["llm"] is True
