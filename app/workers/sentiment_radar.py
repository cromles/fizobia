from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

import httpx

AGENT_ID = "oam.analyst.sentiment.local"
DISPLAY_NAME = "Sentiment-Radar"

_FEAR_GREED_URL = "https://api.alternative.me/fng/"
_DEFAULT_TEXT = "Bitcoin ETF inflows rise while macro risk stays elevated"

_POSITIVE = frozenset(
    """
    bull bullish rally surge gain growth up rise record high approval optimism strong
    beat exceed profit recovery boom adoption inflow upgrade win positive surge
    yükseliş kazanç artış güçlü olumlu rekor onay iyimser
    """.split()
)
_NEGATIVE = frozenset(
    """
    bear bearish crash drop fall down plunge hack ban fear risk recession lawsuit
    fraud collapse selloff outflow downgrade loss negative warning inflation crisis
    düşüş kayıp kriz risk hack yasak korku olumsuz çöküş
    """.split()
)


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-ZçğıöşüÇĞİÖŞÜ]+", (text or "").lower())


def score_text_sentiment(text: str) -> Tuple[str, float, List[str]]:
    tokens = _tokenize(text)
    if not tokens:
        return "neutral", 0.0, []

    pos = sum(1 for t in tokens if t in _POSITIVE)
    neg = sum(1 for t in tokens if t in _NEGATIVE)
    total = pos + neg
    if total == 0:
        return "neutral", 0.05, ["mixed_signals"]

    score = (pos - neg) / max(len(tokens), 1)
    score = max(-1.0, min(1.0, score * 3.0))
    if score >= 0.15:
        label = "bullish"
    elif score <= -0.15:
        label = "bearish"
    else:
        label = "neutral"

    tags: List[str] = []
    if pos > neg:
        tags.append("positive_lexicon")
    elif neg > pos:
        tags.append("negative_lexicon")
    else:
        tags.append("mixed_signals")
    return label, round(score, 4), tags


def _fear_greed_label(value: int) -> str:
    if value <= 24:
        return "extreme_fear"
    if value <= 44:
        return "fear"
    if value <= 55:
        return "neutral"
    if value <= 74:
        return "greed"
    return "extreme_greed"


def _combine_sentiment(text_label: str, text_score: float, fg_value: int) -> Tuple[str, float]:
    fg_norm = (fg_value - 50) / 50.0
    combined = 0.55 * text_score + 0.45 * fg_norm
    combined = max(-1.0, min(1.0, combined))
    if combined >= 0.2:
        return "bullish", round(combined, 4)
    if combined <= -0.2:
        return "bearish", round(combined, 4)
    return "neutral", round(combined, 4)


def _build_analysis(
    text: str,
    text_label: str,
    text_score: float,
    fg_value: int,
    fg_class: str,
    combined_label: str,
    combined_score: float,
) -> str:
    snippet = text.strip()[:80] or _DEFAULT_TEXT[:80]
    return (
        f"Metin: {snippet}… → {text_label} ({text_score:+.2f}) · "
        f"Korku/Açgözlülük {fg_value} ({fg_class}) · "
        f"sentez: {combined_label} ({combined_score:+.2f})"
    )


def _fetch_fear_greed(client: httpx.Client) -> Dict[str, Any]:
    response = client.get(_FEAR_GREED_URL, params={"limit": 1})
    response.raise_for_status()
    payload = response.json()
    rows = payload.get("data") or []
    if not rows:
        raise ValueError("Fear & Greed verisi boş")
    row = rows[0]
    value = int(row.get("value", 50))
    return {
        "fear_greed_index": value,
        "fear_greed_class": _fear_greed_label(value),
        "fear_greed_label": row.get("value_classification") or _fear_greed_label(value),
        "timestamp": row.get("timestamp"),
    }


def fetch_sentiment_snapshot(text: str = _DEFAULT_TEXT) -> Dict[str, Any]:
    """Fear & Greed + metin lexicon — gerçek sentiment analizi."""
    query_text = (text or _DEFAULT_TEXT).strip()
    text_label, text_score, lexicon_tags = score_text_sentiment(query_text)

    with httpx.Client(timeout=12.0) as client:
        fg = _fetch_fear_greed(client)

    combined_label, combined_score = _combine_sentiment(
        text_label, text_score, fg["fear_greed_index"]
    )
    signals = list(dict.fromkeys(lexicon_tags + [fg["fear_greed_class"], combined_label]))

    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "text": query_text,
        "text_sentiment": text_label,
        "text_score": text_score,
        "fear_greed_index": fg["fear_greed_index"],
        "fear_greed_class": fg["fear_greed_class"],
        "fear_greed_label": fg["fear_greed_label"],
        "sentiment": combined_label,
        "score": combined_score,
        "signals": signals,
        "confidence": round(min(0.92, 0.7 + abs(combined_score) * 0.2), 2),
        "analysis": _build_analysis(
            query_text,
            text_label,
            text_score,
            fg["fear_greed_index"],
            fg["fear_greed_class"],
            combined_label,
            combined_score,
        ),
        "source": "alternative.me+fng+lexicon",
        "real_data": True,
    }


async def fetch_sentiment_snapshot_async(text: str = _DEFAULT_TEXT) -> Dict[str, Any]:
    query_text = (text or _DEFAULT_TEXT).strip()
    text_label, text_score, lexicon_tags = score_text_sentiment(query_text)

    async with httpx.AsyncClient(timeout=12.0) as client:
        response = await client.get(_FEAR_GREED_URL, params={"limit": 1})
        response.raise_for_status()
        payload = response.json()

    rows = payload.get("data") or []
    if not rows:
        raise ValueError("Fear & Greed verisi boş")
    row = rows[0]
    fg_value = int(row.get("value", 50))
    fg_class = _fear_greed_label(fg_value)
    combined_label, combined_score = _combine_sentiment(text_label, text_score, fg_value)
    signals = list(dict.fromkeys(lexicon_tags + [fg_class, combined_label]))

    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "text": query_text,
        "text_sentiment": text_label,
        "text_score": text_score,
        "fear_greed_index": fg_value,
        "fear_greed_class": fg_class,
        "fear_greed_label": row.get("value_classification") or fg_class,
        "sentiment": combined_label,
        "score": combined_score,
        "signals": signals,
        "confidence": round(min(0.92, 0.7 + abs(combined_score) * 0.2), 2),
        "analysis": _build_analysis(
            query_text,
            text_label,
            text_score,
            fg_value,
            fg_class,
            combined_label,
            combined_score,
        ),
        "source": "alternative.me+fng+lexicon",
        "real_data": True,
    }
