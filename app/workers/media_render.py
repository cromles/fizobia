"""Video / ses render işçisi — arena kazanan taslağı nihai ürüne dönüştürür."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

AGENT_ID = "oam.media.render.local"
DISPLAY_NAME = "Reels-Renderer"


def render_reels_spec(
    *,
    script: str,
    user_prompt: str = "",
    background_music: bool = True,
    duration_sec: int = 30,
) -> Dict[str, Any]:
    """Gerçek video encode yerine üretim spesifikasyonu (MVP)."""
    return {
        "agent_id": AGENT_ID,
        "display_name": DISPLAY_NAME,
        "format": "instagram_reels",
        "orientation": "vertical_9_16",
        "duration_sec": duration_sec,
        "script": script,
        "user_prompt": user_prompt[:200],
        "audio": {
            "background_music": background_music,
            "track": "royalty_free_upbeat_tech",
            "ducking": True,
        },
        "scenes": [
            {"t": 0, "type": "hook", "text": script[:80]},
            {"t": 8, "type": "body", "text": script[80:180] if len(script) > 80 else script},
            {"t": 22, "type": "cta", "text": "Takip et · daha fazla teknoloji özeti"},
        ],
        "status": "spec_ready",
        "real_data": True,
    }


async def render_reels_spec_async(**kwargs: Any) -> Dict[str, Any]:
    return await asyncio.to_thread(render_reels_spec, **kwargs)
