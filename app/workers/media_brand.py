from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from app.llm.prompts import BRAND_TONE_SYSTEM

logger = logging.getLogger(__name__)

AGENT_ID = "oam.media.brand.local"
DISPLAY_NAME = "Brand-Voice"


def craft_brand_copy(*, narrative: str = "", symbol: str = "bitcoin") -> Dict[str, Any]:
    """Marka sesi — sosyal ve tanıtım metni."""
    short = narrative[:180] + "…" if len(narrative) > 180 else narrative
    tagline = "Axium — dijital işçiler, gerçek gelir, kendi ekosistemimiz."
    social = (
        f"🟢 {symbol.upper()} mesh kanıtı canlı.\n"
        f"{short}\n\n"
        f"{tagline}\n"
        "#Axium #OAM #AgentMesh #Web3"
    )
    return {
        "agent_id": AGENT_ID,
        "display_name": DISPLAY_NAME,
        "tagline": tagline,
        "social_post": social,
        "tone": "direct_honest",
        "real_data": True,
    }


async def craft_brand_copy_async(**kwargs: Any) -> Dict[str, Any]:
    return await asyncio.to_thread(craft_brand_copy, **kwargs)


_TONE_STYLES = {
    "corporate": {
        "opener": "Kurumsal bakış açısıyla",
        "voice": "net, güven veren ve ölçülü",
        "cta": "Detaylı analiz için bizimle iletişime geçin.",
    },
    "humorous": {
        "opener": "Ciddiyeti bir kenara bırakalım",
        "voice": "esprili ama bilgili",
        "cta": "Gülmek serbest — paylaşmayı unutma.",
    },
    "technical": {
        "opener": "Teknik derinlikte",
        "voice": "veri odaklı ve kesin",
        "cta": "Ham veri ve metodoloji talep edilebilir.",
    },
}


def polish_article_tone(
    *,
    draft: str = "",
    topic: str = "",
    tone: str = "corporate",
) -> Dict[str, Any]:
    """Müşteri marka sesine göre metin düzenleme."""
    style = _TONE_STYLES.get(tone, _TONE_STYLES["corporate"])
    polished = (
        f"{style['opener']}, {topic or 'konu'} üzerine {style['voice']} bir metin:\n\n"
        f"{draft.strip()}\n\n"
        f"{style['cta']}"
    )
    return {
        "agent_id": AGENT_ID,
        "display_name": DISPLAY_NAME,
        "tone": tone,
        "polished_draft": polished,
        "word_count": len(polished.split()),
        "real_data": True,
    }


async def polish_article_tone_async(
    *,
    draft: str = "",
    topic: str = "",
    tone: str = "corporate",
) -> Dict[str, Any]:
    from app.config import settings

    base = polish_article_tone(draft=draft, topic=topic, tone=tone)
    if not settings.llm_enabled:
        base["source"] = "template"
        return base

    system = BRAND_TONE_SYSTEM.get(tone, BRAND_TONE_SYSTEM["corporate"])
    user = f"Konu: {topic}\n\nDüzenlenecek taslak:\n{draft}"
    try:
        from app.llm.client import chat_completion

        polished, llm_meta = await chat_completion(
            system=system,
            user=user,
            temperature=0.6,
            max_tokens=900,
        )
        base["polished_draft"] = polished
        base["word_count"] = len(polished.split())
        base["source"] = "llm"
        base["llm_meta"] = llm_meta
    except Exception as exc:
        logger.warning("Brand-Voice LLM fallback: %s", exc)
        base["source"] = "template_fallback"
    return base
