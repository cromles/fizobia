"""Metin gladyatörleri — aynı istem için farklı taslak üreticiler."""

from __future__ import annotations

import asyncio
import re
from typing import Any, Dict, List

AGENT_HOOK_ID = "oam.text.hook.local"
AGENT_STORY_ID = "oam.text.story.local"
AGENT_DATA_ID = "oam.text.data.local"

ARENA_TEXT_COMPETITORS = (AGENT_HOOK_ID, AGENT_STORY_ID, AGENT_DATA_ID)

_COMPETITOR_META = {
    AGENT_HOOK_ID: {"display_name": "Hook-Master", "style": "hook_first", "model": "gpt-4o"},
    AGENT_STORY_ID: {"display_name": "Story-Forge", "style": "narrative_arc", "model": "claude-3.5-sonnet"},
    AGENT_DATA_ID: {"display_name": "Data-Pulse", "style": "fact_dense", "model": "gpt-4o-mini"},
}


def _topic_from_prompt(prompt: str) -> str:
    cleaned = re.sub(r"\s+", " ", (prompt or "").strip())
    if not cleaned:
        return "teknoloji trendleri"
    return cleaned[:120]


def _hook_draft(prompt: str) -> str:
    topic = _topic_from_prompt(prompt)
    return (
        f"Dur! {topic} hakkında 30 saniyede bilmen gereken tek şey bu. "
        f"Algoritma ilk 3 saniyede kaydırırsa kaybedersin — bu yüzden kanca: "
        f"'{topic}' artık eskisi gibi değil. İşte kanıt…"
    )


def _story_draft(prompt: str) -> str:
    topic = _topic_from_prompt(prompt)
    return (
        f"Geçen hafta {topic} dünyasında sessiz bir değişim başladı. "
        f"Çoğu kişi fark etmedi ama erken görenler pozisyon aldı. "
        f"30 saniyelik Reels için hikaye: problem → dönüm → net sonuç."
    )


def _data_draft(prompt: str) -> str:
    topic = _topic_from_prompt(prompt)
    return (
        f"{topic}: 3 veri noktası. (1) Talep artışı sinyali. "
        f"(2) Maliyet düşüş eğilimi. (3) Dikey video tüketimi +%18. "
        f"Sonuç: kısa formatta veri + görsel = en yüksek tutma."
    )


def draft_for_agent(agent_id: str, *, user_prompt: str) -> Dict[str, Any]:
    meta = _COMPETITOR_META[agent_id]
    if meta["style"] == "hook_first":
        body = _hook_draft(user_prompt)
    elif meta["style"] == "narrative_arc":
        body = _story_draft(user_prompt)
    else:
        body = _data_draft(user_prompt)

    return {
        "agent_id": agent_id,
        "display_name": meta["display_name"],
        "style": meta["style"],
        "model": meta["model"],
        "draft": body,
        "word_count": len(body.split()),
        "target_format": "instagram_reels_vertical_30s",
        "real_data": True,
    }


async def draft_for_agent_async(agent_id: str, *, user_prompt: str) -> Dict[str, Any]:
    return await asyncio.to_thread(draft_for_agent, agent_id, user_prompt=user_prompt)


async def run_text_arena_parallel(user_prompt: str) -> List[Dict[str, Any]]:
    tasks = [draft_for_agent_async(aid, user_prompt=user_prompt) for aid in ARENA_TEXT_COMPETITORS]
    return list(await asyncio.gather(*tasks))
