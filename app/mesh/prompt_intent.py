"""İstem türü — Reels arenası mı, uzman metin üretimi mi?"""

from __future__ import annotations

import re

_REELS_HINTS = re.compile(
    r"reels|instagram|tiktok|shorts|\bvideo\b|30\s*saniye|dikey|kanca|montaj|\breel\b",
    re.I,
)
_POEM_HINTS = re.compile(r"şiir|siir|poem|lyric|dize|kıta|kita|aşk\s*şiiri", re.I)
_PROSE_HINTS = re.compile(
    r"makale|article|essay|blog|hikaye|metin\s*yaz|yaz\s*bana|copywriting",
    re.I,
)


def is_reels_intent(prompt: str) -> bool:
    return bool(_REELS_HINTS.search(prompt))


def compose_kind(prompt: str) -> str:
    """poem | prose | general"""
    if _POEM_HINTS.search(prompt):
        return "poem"
    if _PROSE_HINTS.search(prompt):
        return "prose"
    return "general"


def prompt_mode(prompt: str) -> str:
    """arena yalnızca açık Reels/video isteği; geri kalan her şey uzman compose."""
    if is_reels_intent(prompt):
        return "arena"
    return "quick_compose"
