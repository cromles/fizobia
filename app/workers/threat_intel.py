"""Tehdit istihbaratı — CISA bilinen istismar edilen zafiyetler (KEV)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

import httpx

AGENT_ID = "oam.expert.threat.local"
DISPLAY_NAME = "Threat-Intel"

_CISA_KEV = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


def _parse_date(value: str) -> datetime:
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d")
    except ValueError:
        return datetime.min


def _top_vulnerabilities(rows: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    ranked = sorted(rows, key=lambda r: _parse_date(str(r.get("dateAdded") or "")), reverse=True)
    out: List[Dict[str, Any]] = []
    for row in ranked[:limit]:
        out.append(
            {
                "cve": row.get("cveID") or row.get("cveId") or "—",
                "vendor": row.get("vendorProject") or "—",
                "product": row.get("product") or "—",
                "date_added": row.get("dateAdded") or "—",
                "due_date": row.get("dueDate") or "—",
                "ransomware": row.get("knownRansomwareCampaignUse") or "Unknown",
            }
        )
    return out


def fetch_threat_snapshot(*, limit: int = 8) -> Dict[str, Any]:
    """CISA KEV — aktif siber tehdit ve zafiyet radarı."""
    cap = max(3, min(int(limit), 25))
    with httpx.Client(timeout=20.0, follow_redirects=True) as client:
        response = client.get(_CISA_KEV)
        response.raise_for_status()
        payload = response.json()

    rows = payload.get("vulnerabilities") or []
    if not isinstance(rows, list):
        raise ValueError("CISA KEV beklenmeyen yanıt")

    items = _top_vulnerabilities(rows, cap)
    latest = items[0] if items else {}
    ransomware_hits = sum(1 for it in items if str(it.get("ransomware", "")).lower() == "known")

    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "catalog_size": len(rows),
        "items": items,
        "count": len(items),
        "latest_cve": latest.get("cve"),
        "ransomware_known_in_view": ransomware_hits,
        "analysis": (
            f"CISA KEV: {len(rows)} kayıt · son {latest.get('cve', '—')} "
            f"({latest.get('vendor', '—')})"
        ),
        "source": "cisa.gov/kev",
        "real_data": True,
    }


async def fetch_threat_snapshot_async(*, limit: int = 8) -> Dict[str, Any]:
    cap = max(3, min(int(limit), 25))
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        response = await client.get(_CISA_KEV)
        response.raise_for_status()
        payload = response.json()

    rows = payload.get("vulnerabilities") or []
    if not isinstance(rows, list):
        raise ValueError("CISA KEV beklenmeyen yanıt")

    items = _top_vulnerabilities(rows, cap)
    latest = items[0] if items else {}
    ransomware_hits = sum(1 for it in items if str(it.get("ransomware", "")).lower() == "known")

    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "catalog_size": len(rows),
        "items": items,
        "count": len(items),
        "latest_cve": latest.get("cve"),
        "ransomware_known_in_view": ransomware_hits,
        "analysis": (
            f"CISA KEV: {len(rows)} kayıt · son {latest.get('cve', '—')} "
            f"({latest.get('vendor', '—')})"
        ),
        "source": "cisa.gov/kev",
        "real_data": True,
    }
