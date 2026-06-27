from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from html import unescape
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx

AGENT_ID = "oam.fetcher.web.local"
DISPLAY_NAME = "Web-Crawler-Pro"

_DEFAULT_RSS = "https://www.coindesk.com/arc/outboundfeeds/rss/"
_USER_AGENT = "OAM-WebCrawler/1.0 (+https://github.com/cromles/fizobia)"


def _strip_html(html: str) -> str:
    cleaned = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<style[^>]*>.*?</style>", " ", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    return re.sub(r"\s+", " ", unescape(cleaned)).strip()


def _parse_rss_items(xml_text: str, limit: int = 12) -> List[Dict[str, str]]:
    root = ET.fromstring(xml_text)
    items: List[Dict[str, str]] = []
    for item in root.findall(".//item")[:limit]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = item.findtext("description") or ""
        snippet = _strip_html(description)[:280]
        if title:
            items.append({"title": title, "link": link, "snippet": snippet})
    if items:
        return items
    for item in root.findall(".//{http://www.w3.org/2005/Atom}entry")[:limit]:
        title = (item.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
        link_el = item.find("{http://www.w3.org/2005/Atom}link")
        link = link_el.attrib.get("href", "") if link_el is not None else ""
        summary = item.findtext("{http://www.w3.org/2005/Atom}summary") or ""
        snippet = _strip_html(summary)[:280]
        if title:
            items.append({"title": title, "link": link, "snippet": snippet})
    if not items:
        raise ValueError("RSS akışında haber bulunamadı")
    return items


def _parse_rss(xml_text: str) -> Dict[str, str]:
    items = _parse_rss_items(xml_text, limit=1)
    first = items[0]
    return {"title": first["title"], "link": first["link"], "snippet": first["snippet"]}


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Sadece http/https URL desteklenir")
    if not parsed.netloc:
        raise ValueError("Geçersiz URL")
    return url


def fetch_web_snapshot(url: Optional[str] = None) -> Dict[str, Any]:
    """Gerçek web/RSS kaynağından canlı veri çeker."""
    target = _validate_url(url) if url else _DEFAULT_RSS
    headers = {"User-Agent": _USER_AGENT, "Accept": "application/rss+xml, text/html, */*"}

    with httpx.Client(timeout=15.0, follow_redirects=True, headers=headers) as client:
        response = client.get(target)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").lower()
        body = response.text

    if "xml" in content_type or target.endswith(".rss") or "<rss" in body[:300].lower():
        parsed = _parse_rss(body)
        headline = parsed["title"]
        snippet = parsed["snippet"]
        source_url = parsed["link"] or target
        source_kind = "rss"
    else:
        text = _strip_html(body)
        headline_match = re.search(r"<title[^>]*>([^<]+)</title>", body, re.I)
        headline = unescape(headline_match.group(1)).strip() if headline_match else urlparse(target).netloc
        snippet = text[:400]
        source_url = target
        source_kind = "html"

    if not snippet:
        raise ValueError("Sayfadan metin çıkarılamadı")

    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "url": source_url,
        "headline": headline,
        "snippet": snippet,
        "chars": len(snippet),
        "source_kind": source_kind,
        "analysis": f"Çekildi: {headline[:90]}… ({len(snippet)} karakter)",
        "source": source_url,
        "real_data": True,
    }


async def fetch_web_feed_async(url: Optional[str] = None, *, limit: int = 12) -> Dict[str, Any]:
    """RSS/HTML kaynağından birden fazla haber başlığı."""
    target = _validate_url(url) if url else _DEFAULT_RSS
    headers = {"User-Agent": _USER_AGENT, "Accept": "application/rss+xml, text/html, */*"}

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=headers) as client:
        response = await client.get(target)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").lower()
        body = response.text

    if "xml" in content_type or target.endswith(".rss") or "<rss" in body[:300].lower():
        items = _parse_rss_items(body, limit=limit)
        source_kind = "rss"
    else:
        text = _strip_html(body)
        headline_match = re.search(r"<title[^>]*>([^<]+)</title>", body, re.I)
        headline = unescape(headline_match.group(1)).strip() if headline_match else urlparse(target).netloc
        items = [{"title": headline, "link": target, "snippet": text[:280]}]
        source_kind = "html"

    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "feed_url": target,
        "source_kind": source_kind,
        "items": items,
        "count": len(items),
        "real_data": True,
    }


async def fetch_web_snapshot_async(url: Optional[str] = None) -> Dict[str, Any]:
    target = _validate_url(url) if url else _DEFAULT_RSS
    headers = {"User-Agent": _USER_AGENT, "Accept": "application/rss+xml, text/html, */*"}

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=headers) as client:
        response = await client.get(target)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").lower()
        body = response.text

    if "xml" in content_type or target.endswith(".rss") or "<rss" in body[:300].lower():
        parsed = _parse_rss(body)
        headline = parsed["title"]
        snippet = parsed["snippet"]
        source_url = parsed["link"] or target
        source_kind = "rss"
    else:
        text = _strip_html(body)
        headline_match = re.search(r"<title[^>]*>([^<]+)</title>", body, re.I)
        headline = unescape(headline_match.group(1)).strip() if headline_match else urlparse(target).netloc
        snippet = text[:400]
        source_url = target
        source_kind = "html"

    if not snippet:
        raise ValueError("Sayfadan metin çıkarılamadı")

    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "url": source_url,
        "headline": headline,
        "snippet": snippet,
        "chars": len(snippet),
        "source_kind": source_kind,
        "analysis": f"Çekildi: {headline[:90]}… ({len(snippet)} karakter)",
        "source": source_url,
        "real_data": True,
    }
