"""İstem türü — Reels arenası mı, hızlı metin üretimi mi?"""

from __future__ import annotations

import re

_REELS_HINTS = re.compile(
    r"reels|instagram|tiktok|shorts|video|30\s*saniye|dikey|kanca|montaj|reel",
    re.I,
)
_COMPOSE_HINTS = re.compile(
    r"şiir|siir|poem|makale|article|hikaye|story|essay|metin\s*yaz|yaz\s*bana|copywriting|blog|aşk|ask",
    re.I,
)


def is_reels_intent(prompt: str) -> bool:
    return bool(_REELS_HINTS.search(prompt))


def is_quick_compose_intent(prompt: str) -> bool:
    if is_reels_intent(prompt):
        return False
    return bool(_COMPOSE_HINTS.search(prompt))


def prompt_mode(prompt: str) -> str:
    """arena | quick_compose"""
    if is_quick_compose_intent(prompt):
        return "quick_compose"
    return "arena"
