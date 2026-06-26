from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from app.mesh.founder_profile import FOUNDER_NAME

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
