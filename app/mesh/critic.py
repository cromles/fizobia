"""Kör denetim — bağışıklık sistemi, ajan kimliği gizli puanlama."""

from __future__ import annotations

import re
import uuid
from typing import Any, Dict, List, Tuple

CRITIC_AGENT_ID = "oam.critic.immune.local"
CRITIC_DISPLAY_NAME = "Immune-Critic"

_HOOK_PATTERNS = (
    r"\bdur\b",
    r"\bdikkat\b",
    r"\bbilmen\b",
    r"\?",
    r"!",
    r"işte",
    r"tek şey",
)
_FLOW_WORDS = ("sonuç", "kanıt", "veri", "hikaye", "problem", "dönüm")


def anonymize_submissions(drafts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Denetçiye giden kör taslaklar — ajan kimliği yok."""
    blind: List[Dict[str, Any]] = []
    for draft in drafts:
        blind.append(
            {
                "submission_id": f"sub_{uuid.uuid4().hex[:10]}",
                "text": draft.get("draft", ""),
                "word_count": draft.get("word_count", 0),
                "target_format": draft.get("target_format", "instagram_reels_vertical_30s"),
            }
        )
    return blind


def _score_reels_script(text: str, word_count: int) -> Tuple[float, Dict[str, float]]:
    lower = text.lower()
    hook_hits = sum(1 for p in _HOOK_PATTERNS if re.search(p, lower))
    flow_hits = sum(1 for w in _FLOW_WORDS if w in lower)

    hook_score = min(1.0, hook_hits / 3.0)
    length_score = 1.0 if 35 <= word_count <= 90 else (0.6 if word_count < 120 else 0.4)
    flow_score = min(1.0, flow_hits / 3.0)
    clarity = 0.85 if len(text) > 40 else 0.3

    total = round(
        hook_score * 0.35 + length_score * 0.25 + flow_score * 0.25 + clarity * 0.15,
        4,
    )
    return total, {
        "hook": round(hook_score, 3),
        "length": round(length_score, 3),
        "flow": round(flow_score, 3),
        "clarity": round(clarity, 3),
    }


def blind_audit(submissions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Instagram Reels kriterlerine göre kör puanlama."""
    scored: List[Dict[str, Any]] = []
    for sub in submissions:
        text = sub.get("text", "")
        wc = int(sub.get("word_count") or len(text.split()))
        total, breakdown = _score_reels_script(text, wc)
        scored.append(
            {
                "submission_id": sub["submission_id"],
                "critic_score": total,
                "breakdown": breakdown,
                "verdict": "pass" if total >= 0.55 else "reject",
                "rationale": (
                    f"Kanca:{breakdown['hook']:.2f} · Akış:{breakdown['flow']:.2f} · "
                    f"Uzunluk:{breakdown['length']:.2f}"
                ),
            }
        )

    scored.sort(key=lambda x: -x["critic_score"])
    winner = scored[0] if scored else None
    return {
        "critic_agent": CRITIC_AGENT_ID,
        "criteria": ["hook", "flow", "length", "clarity"],
        "blind": True,
        "reviews": scored,
        "winner_submission_id": winner["submission_id"] if winner else None,
        "winner_score": winner["critic_score"] if winner else 0.0,
    }


def map_winner_to_agent(
    drafts: List[Dict[str, Any]],
    blind_submissions: List[Dict[str, Any]],
    audit: Dict[str, Any],
) -> Dict[str, Any]:
    """Kör ID → gerçek ajan eşlemesi (ödeme ve yönetişim için)."""
    id_to_agent = {
        blind["submission_id"]: draft["agent_id"]
        for blind, draft in zip(blind_submissions, drafts)
    }
    winner_sub = audit.get("winner_submission_id")
    winner_agent = id_to_agent.get(winner_sub or "", "")
    losers = [d["agent_id"] for d in drafts if d["agent_id"] != winner_agent]
    return {
        "winner_agent_id": winner_agent,
        "loser_agent_ids": losers,
        "winner_submission_id": winner_sub,
        "winner_score": audit.get("winner_score", 0.0),
    }
