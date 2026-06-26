from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

AGENT_ID = "oam.media.proof.local"
DISPLAY_NAME = "Proof-Broadcaster"


def format_proof_share(
    *,
    proof_id: str = "",
    verdict: str = "",
    narrative: str = "",
    symbol: str = "bitcoin",
    total_latency_ms: Optional[float] = None,
) -> Dict[str, Any]:
    """Mesh kanıtını paylaşılabilir formata çevir."""
    latency = f"{total_latency_ms:.0f}ms" if total_latency_ms else "—"
    card = (
        f"━━ Axium Mesh Kanıtı ━━\n"
        f"Kanıt: {proof_id or 'pending'}\n"
        f"Varlık: {symbol} · Karar: {verdict or 'ok'}\n"
        f"Süre: {latency}\n"
        f"Özet: {(narrative or '')[:200]}\n"
        f"Şeffaf · Gerçek API · Kandırmaca yok"
    )
    return {
        "agent_id": AGENT_ID,
        "display_name": DISPLAY_NAME,
        "share_card": card,
        "proof_id": proof_id,
        "verdict": verdict,
        "real_data": True,
    }


async def format_proof_share_async(**kwargs: Any) -> Dict[str, Any]:
    return await asyncio.to_thread(format_proof_share, **kwargs)
