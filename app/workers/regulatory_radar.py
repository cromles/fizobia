"""Düzenleme radarı — kripto politika ve regülasyon haber akışı."""

from __future__ import annotations

import re
from html import unescape
from typing import Any, Dict, List
import xml.etree.ElementTree as ET

import httpx

AGENT_ID = "oam.expert.regulatory.local"
DISPLAY_NAME = "Regulatory-Radar"

_DEFAULT_RSS = "https://www.coindesk.com/arc/outboundfeeds/rss/"
_USER_AGENT = "OAM-Regulatory-Radar/1.0 (+https://github.com/cromles/fizobia)"
_KEYWORDS = re.compile(
    r"\b(sec|cftc|regulat|policy|law|bill|ban|approve|etf|mica|compliance|"
    r"sanction|lawsuit|court|congress|parliament|treasury|fed|cbdc)\b",
    re.I,
)


def _strip_html(html: str) -> str:
    cleaned = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", unescape(cleaned)).strip()


def _parse_rss_items(xml_text: str, limit: int = 20) -> List[Dict[str, str]]:
    root = ET.fromstring(xml_text)
    items: List[Dict[str, str]] = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = item.findtext("description") or ""
        snippet = _strip_html(description)[:280]
        if title:
            items.append({"title": title, "link": link, "snippet": snippet})
    if not items:
        for item in root.findall(".//{http://www.w3.org/2005/Atom}entry"):
            title = (item.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
            link_el = item.find("{http://www.w3.org/2005/Atom}link")
            link = link_el.attrib.get("href", "") if link_el is not None else ""
            summary = item.findtext("{http://www.w3.org/2005/Atom}summary") or ""
            snippet = _strip_html(summary)[:280]
            if title:
                items.append({"title": title, "link": link, "snippet": snippet})
    return items[:limit]


def _filter_regulatory(items: List[Dict[str, str]], limit: int) -> List[Dict[str, str]]:
    matched = [it for it in items if _KEYWORDS.search(it.get("title", "") + " " + it.get("snippet", ""))]
    if len(matched) < limit // 2:
        matched = items[:limit]
    return matched[:limit]


def fetch_regulatory_feed(*, limit: int = 8) -> Dict[str, Any]:
    """CoinDesk RSS üzerinden düzenleme odaklı haber filtresi."""
    cap = max(3, min(int(limit), 20))
    headers = {"User-Agent": _USER_AGENT, "Accept": "application/rss+xml, */*"}

    with httpx.Client(timeout=15.0, follow_redirects=True, headers=headers) as client:
        response = client.get(_DEFAULT_RSS)
        response.raise_for_status()
        raw_items = _parse_rss_items(response.text, limit=40)

    items = _filter_regulatory(raw_items, cap)
    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "feed_url": _DEFAULT_RSS,
        "items": items,
        "count": len(items),
        "filter": "policy/regulation keywords",
        "analysis": f"{len(items)} düzenleme sinyali — SEC, ETF, politika, uyum",
        "source": "coindesk-rss",
        "real_data": True,
    }


async def fetch_regulatory_feed_async(*, limit: int = 8) -> Dict[str, Any]:
    cap = max(3, min(int(limit), 20))
    headers = {"User-Agent": _USER_AGENT, "Accept": "application/rss+xml, */*"}

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=headers) as client:
        response = await client.get(_DEFAULT_RSS)
        response.raise_for_status()
        raw_items = _parse_rss_items(response.text, limit=40)

    items = _filter_regulatory(raw_items, cap)
    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "feed_url": _DEFAULT_RSS,
        "items": items,
        "count": len(items),
        "filter": "policy/regulation keywords",
        "analysis": f"{len(items)} düzenleme sinyali — SEC, ETF, politika, uyum",
        "source": "coindesk-rss",
        "real_data": True,
    }
