from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from app.llm.prompts import ARTICLE_OUTLINE_SYSTEM
from app.mesh.founder_profile import FOUNDER_NAME

logger = logging.getLogger(__name__)

AGENT_ID = "oam.media.story.local"
DISPLAY_NAME = "Story-Weaver"


def weave_story(
    *,
    symbol: str = "bitcoin",
    verdict: str = "",
    headline: str = "",
    sentiment: str = "",
    price_usd: Optional[float] = None,
    proof_id: str = "",
) -> Dict[str, Any]:
    """Axium hikayesi — kurucu, aile, gerçek mesh kanıtı."""
    hook = headline[:100] if headline else f"{symbol.upper()} piyasası canlı"
    mood = sentiment or verdict or "aktif"
    price_bit = f" Fiyat: ${price_usd:,.0f}." if price_usd else ""
    narrative = (
        f"{FOUNDER_NAME} liderliğindeki Axium ailesi, {symbol} için gerçek mesh kanıtı üretti. "
        f"{hook}. Sentiment: {mood}.{price_bit} "
        "Uydurma yok — dijital işçiler konuşarak çalıştı. Sıfırdan imparatorluk inşa ediyoruz."
    )
    return {
        "agent_id": AGENT_ID,
        "display_name": DISPLAY_NAME,
        "narrative": narrative,
        "headline": f"Axium Mesh Kanıtı — {symbol}",
        "proof_id": proof_id,
        "founder": FOUNDER_NAME,
        "real_data": True,
    }


async def weave_story_async(**kwargs: Any) -> Dict[str, Any]:
    return await asyncio.to_thread(weave_story, **kwargs)


def weave_article_outline(
    *,
    topic: str = "",
    headline: str = "",
    snippet: str = "",
    source_url: str = "",
) -> Dict[str, Any]:
    """Araştırma verisinden makale iskeleti — giriş, gelişme, sonuç."""
    hook = headline or topic or "Güncel gelişmeler"
    body_seed = snippet[:320] if snippet else f"{topic} hakkında güncel veriler toplandı."
    intro = (
        f"Giriş — {hook}. Okuyucunun dikkatini çeken kanca: "
        f"bu konu neden şimdi önemli ve kimleri etkiliyor?"
    )
    development = (
        f"Gelişme — {body_seed} "
        "Veri noktaları, bağlam ve sektör etkisi burada açılıyor. "
        "Kaynaklar çapraz doğrulandı."
    )
    conclusion = (
        f"Sonuç — {topic or hook} için net özet: trend devam ediyor mu, "
        "yatırımcı ve okuyucu ne yapmalı? Bir sonraki adımı belirt."
    )
    draft = f"{intro}\n\n{development}\n\n{conclusion}"
    return {
        "agent_id": AGENT_ID,
        "display_name": DISPLAY_NAME,
        "topic": topic,
        "headline": hook,
        "outline": {"intro": intro, "development": development, "conclusion": conclusion},
        "draft": draft,
        "word_count": len(draft.split()),
        "source_url": source_url,
        "real_data": True,
    }


async def weave_article_outline_async(
    *,
    topic: str = "",
    headline: str = "",
    snippet: str = "",
    source_url: str = "",
) -> Dict[str, Any]:
    from app.config import settings

    base = weave_article_outline(
        topic=topic, headline=headline, snippet=snippet, source_url=source_url
    )
    if not settings.llm_enabled:
        base["source"] = "template"
        return base

    user = (
        f"Konu: {topic}\n"
        f"Başlık: {headline}\n"
        f"Araştırma özeti: {snippet}\n"
        f"Kaynak: {source_url}"
    )
    try:
        from app.llm.client import chat_completion

        draft, llm_meta = await chat_completion(
            system=ARTICLE_OUTLINE_SYSTEM,
            user=user,
            temperature=0.65,
            max_tokens=700,
        )
        base["draft"] = draft
        base["word_count"] = len(draft.split())
        base["outline"] = {"full": draft}
        base["source"] = "llm"
        base["llm_meta"] = llm_meta
    except Exception as exc:
        logger.warning("Makale LLM fallback: %s", exc)
        base["source"] = "template_fallback"
    return base
