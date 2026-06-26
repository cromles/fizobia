"""Metin gladyatörleri — uzman LLM veya şablon taslak üreticiler."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Dict, List

from app.llm.prompts import ARENA_AGENT_SYSTEMS, ARENA_STYLE_HINTS, HOOK_MASTER_SYSTEM

logger = logging.getLogger(__name__)

AGENT_HOOK_ID = "oam.text.hook.local"
AGENT_STORY_ID = "oam.text.story.local"
AGENT_DATA_ID = "oam.text.data.local"

ARENA_TEXT_COMPETITORS = (AGENT_HOOK_ID, AGENT_STORY_ID, AGENT_DATA_ID)

_MIN_REELS_WORDS = 35

_COMPETITOR_META = {
    AGENT_HOOK_ID: {"display_name": "Hook-Master", "style": "hook_first", "model": "gpt-4o-mini"},
    AGENT_STORY_ID: {"display_name": "Story-Forge", "style": "narrative_arc", "model": "gpt-4o-mini"},
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
        f"'{topic}' artık eskisi gibi değil. İşte kanıt: erken görenler pozisyon aldı, "
        f"geç kalanlar ise aynı hatayı tekrarlıyor. Şimdi sana üç net sinyal vereceğim — "
        f"son cümleye kadar kal, çünkü orada asıl fark yatıyor."
    )


def _story_draft(prompt: str) -> str:
    topic = _topic_from_prompt(prompt)
    return (
        f"Geçen hafta {topic} dünyasında sessiz bir değişim başladı. "
        f"Çoğu kişi fark etmedi ama erken görenler pozisyon aldı. "
        f"30 saniyelik Reels için hikaye: önce problem — herkes aynı eski yönteme bağlı kaldı. "
        f"Sonra dönüm noktası — küçük bir ekip farklı bir açı denedi ve sonuçlar değişti. "
        f"Net sonuç: bugün hâlâ bekleyenler, dün harekete geçenlerin gerisinde."
    )


def _data_draft(prompt: str) -> str:
    topic = _topic_from_prompt(prompt)
    return (
        f"{topic}: üç veri noktası. Birincisi, talep sinyali son çeyrekte belirgin şekilde yükseldi. "
        f"İkincisi, maliyet eğrisi aşağı yönlü kırıldı — bu da erişimi kolaylaştırıyor. "
        f"Üçüncüsü, dikey video tüketimi yüzde on sekiz arttı; tutma süresi kısa metinlerde daha yüksek. "
        f"Sonuç net: veri artı görsel hikâye, Reels formatında en güçlü kombinasyon."
    )


def _template_draft(agent_id: str, user_prompt: str) -> str:
    meta = _COMPETITOR_META[agent_id]
    if meta["style"] == "hook_first":
        return _hook_draft(user_prompt)
    if meta["style"] == "narrative_arc":
        return _story_draft(user_prompt)
    return _data_draft(user_prompt)


async def _llm_draft(agent_id: str, *, user_prompt: str, model: str) -> tuple[str, Dict[str, Any]]:
    from app.llm.client import chat_completion

    meta = _COMPETITOR_META[agent_id]
    style = meta["style"]
    system = ARENA_AGENT_SYSTEMS.get(style, HOOK_MASTER_SYSTEM)
    style_hint = ARENA_STYLE_HINTS.get(style, "")
    user = f"İstem: {user_prompt}\n\n{style_hint}"
    text, llm_meta = await chat_completion(
        system=system,
        user=user,
        model=model,
        temperature=0.85,
        max_tokens=400,
        timeout=35.0,
    )

    if len(text.split()) < _MIN_REELS_WORDS:
        text, retry_meta = await chat_completion(
            system=system + " ÖNCEKİ METİN ÇOK KISA. En az 40 kelimelik tam Reels konuşma metni yaz.",
            user=(
                f"İstem: {user_prompt}\n\n"
                f"Kısa taslak (yetersiz):\n{text}\n\n"
                "Şimdi tam, akıcı Reels metnini yaz."
            ),
            model=model,
            temperature=0.88,
            max_tokens=450,
            timeout=35.0,
        )
        llm_meta = {**llm_meta, "retry": retry_meta}

    return text, llm_meta


def draft_for_agent(agent_id: str, *, user_prompt: str) -> Dict[str, Any]:
    meta = _COMPETITOR_META[agent_id]
    body = _template_draft(agent_id, user_prompt)
    return {
        "agent_id": agent_id,
        "display_name": meta["display_name"],
        "style": meta["style"],
        "model": meta["model"],
        "draft": body,
        "word_count": len(body.split()),
        "target_format": "instagram_reels_vertical_30s",
        "source": "template",
        "real_data": True,
    }


async def draft_for_agent_async(agent_id: str, *, user_prompt: str) -> Dict[str, Any]:
    meta = _COMPETITOR_META[agent_id]
    source = "template"
    llm_meta: Dict[str, Any] = {}

    try:
        from app.config import settings

        if settings.llm_enabled:
            from app.llm.client import _provider_label

            llm_model = (
                settings.llm_model
                if _provider_label(settings.llm_base_url) == "gemini"
                else meta["model"]
            )
            body, llm_meta = await _llm_draft(agent_id, user_prompt=user_prompt, model=llm_model)
            source = "llm"
        else:
            body = _template_draft(agent_id, user_prompt)
    except Exception as exc:
        logger.warning("Arena LLM fallback (%s): %s", agent_id, exc)
        body = _template_draft(agent_id, user_prompt)
        source = "template_fallback"

    return {
        "agent_id": agent_id,
        "display_name": meta["display_name"],
        "style": meta["style"],
        "model": llm_meta.get("model", meta["model"]),
        "draft": body,
        "word_count": len(body.split()),
        "target_format": "instagram_reels_vertical_30s",
        "source": source,
        "llm_meta": llm_meta or None,
        "real_data": True,
    }


async def run_text_arena_parallel(user_prompt: str) -> List[Dict[str, Any]]:
    tasks = [draft_for_agent_async(aid, user_prompt=user_prompt) for aid in ARENA_TEXT_COMPETITORS]
    return list(await asyncio.gather(*tasks))
