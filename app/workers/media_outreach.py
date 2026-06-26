from __future__ import annotations

import asyncio
from typing import Any, Dict

from app.mesh.founder_profile import FOUNDER_NAME

AGENT_ID = "oam.media.outreach.local"
DISPLAY_NAME = "Outreach-Pulse"


def build_outreach_pitch(
    *,
    tagline: str = "",
    symbol: str = "bitcoin",
    proof_id: str = "",
) -> Dict[str, Any]:
    """Topluluk ve yatırımcıya kısa yol pitch."""
    pitch = (
        f"Merhaba — {FOUNDER_NAME}, Axium ailesi. "
        f"Gerçek dijital işçi mesh'i: {symbol} kanıtı {proof_id or 'canlı'}. "
        f"{tagline or 'Pasif stake, x402 gelir, şeffaf kanıt.'} "
        "Dev şirketlerin kölesi değiliz — kendi ekosistemimizi kuruyoruz. "
        "Sermayeye kısa yoldan: hub.canlı kanıt + stake."
    )
    return {
        "agent_id": AGENT_ID,
        "display_name": DISPLAY_NAME,
        "pitch": pitch,
        "audience": ["community", "micro_investor", "operator"],
        "cta": "hub/ecosystem · mesh proof · stake",
        "real_data": True,
    }


async def build_outreach_pitch_async(**kwargs: Any) -> Dict[str, Any]:
    return await asyncio.to_thread(build_outreach_pitch, **kwargs)
