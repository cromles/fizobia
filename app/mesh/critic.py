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


_MIN_REELS_WORDS = 35


def _score_reels_script(text: str, word_count: int) -> Tuple[float, Dict[str, float]]:
    lower = text.lower()
    hook_hits = sum(1 for p in _HOOK_PATTERNS if re.search(p, lower))
    flow_hits = sum(1 for w in _FLOW_WORDS if w in lower)

    hook_score = min(1.0, hook_hits / 3.0)
    if word_count < 20:
        length_score = 0.08
    elif word_count < _MIN_REELS_WORDS:
        length_score = 0.28
    elif word_count <= 90:
        length_score = 1.0
    elif word_count <= 120:
        length_score = 0.65
    else:
        length_score = 0.4
    flow_score = min(1.0, flow_hits / 3.0)
    if word_count >= _MIN_REELS_WORDS:
        clarity = 0.9
    elif word_count >= 20:
        clarity = 0.45
    else:
        clarity = 0.12

    total = round(
        hook_score * 0.35 + length_score * 0.3 + flow_score * 0.25 + clarity * 0.1,
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
                "verdict": (
                    "pass"
                    if total >= 0.55 and wc >= _MIN_REELS_WORDS
                    else "reject"
                ),
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


_ARTICLE_SECTION_MARKERS = ("giriş", "gelişme", "sonuç", "özet", "kaynak")
_GRAMMAR_HINTS = (".", ",", ":", "—", "ve", "ile", "için")


def _score_article(text: str, word_count: int) -> Tuple[float, Dict[str, float]]:
    lower = text.lower()
    section_hits = sum(1 for m in _ARTICLE_SECTION_MARKERS if m in lower)
    grammar_hits = sum(1 for g in _GRAMMAR_HINTS if g in text)
    length_score = 1.0 if 180 <= word_count <= 900 else (0.7 if word_count >= 120 else 0.4)
    structure_score = min(1.0, section_hits / 2.0)
    flow_score = min(1.0, grammar_hits / 6.0)
    clarity = 0.9 if len(text) > 200 else 0.35

    total = round(
        length_score * 0.3 + structure_score * 0.3 + flow_score * 0.2 + clarity * 0.2,
        4,
    )
    return total, {
        "length": round(length_score, 3),
        "structure": round(structure_score, 3),
        "flow": round(flow_score, 3),
        "clarity": round(clarity, 3),
    }


def audit_article(text: str) -> Dict[str, Any]:
    """Makale kalite kapısı — yazım, akış ve yapı denetimi."""
    wc = len(text.split())
    total, breakdown = _score_article(text, wc)
    passed = total >= 0.58
    return {
        "critic_agent": CRITIC_AGENT_ID,
        "criteria": ["length", "structure", "flow", "clarity"],
        "blind": False,
        "word_count": wc,
        "critic_score": total,
        "breakdown": breakdown,
        "verdict": "pass" if passed else "reject",
        "rationale": (
            f"Yapı:{breakdown['structure']:.2f} · Akış:{breakdown['flow']:.2f} · "
            f"Uzunluk:{breakdown['length']:.2f} · Netlik:{breakdown['clarity']:.2f}"
        ),
        "approved": passed,
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
