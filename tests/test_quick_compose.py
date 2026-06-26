"""Hızlı metin ve istem yönlendirme testleri."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.mesh.prompt_intent import compose_kind, prompt_mode
from app.mesh.quick_compose import run_quick_compose


def test_poem_routes_quick_compose():
    assert prompt_mode("bana şiir yaz aşk şiiri olsun") == "quick_compose"
    assert compose_kind("bana şiir yaz aşk şiiri olsun") == "poem"


def test_general_text_routes_quick_compose():
    assert prompt_mode("bana güzel bir metin yaz") == "quick_compose"


def test_reels_stays_arena():
    assert prompt_mode("30 saniyelik instagram reels metni") == "arena"


@pytest.mark.asyncio
async def test_quick_compose_template():
    from dataclasses import replace
    from app.config import settings

    with patch("app.config.settings", replace(settings, llm_api_key="")):
        result = await run_quick_compose(user_prompt="bana aşk şiiri yaz")
    assert result["mode"] == "quick_compose"
    assert result["compose_kind"] == "poem"
    assert result["winner"]["script"]
    assert len(result["winner"]["script"].splitlines()) >= 8
    assert result["total_latency_ms"] < 500
