from __future__ import annotations

import asyncio
from typing import Any, Dict

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
