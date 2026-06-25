from __future__ import annotations

import html
from typing import List, Optional

from app.investment.schemas import AgentIdentityCard
from app.protocol.schemas import AgentManifest

CLASS_LABELS = {
    "fetcher": "Veri",
    "transformer": "Dönüştürücü",
    "synthesizer": "Sentez",
    "analyst": "Analist",
    "validator": "Doğrulayıcı",
    "orchestrator": "Orkestratör",
}

CLASS_ICONS = {
    "fetcher": "⬡",
    "transformer": "◈",
    "synthesizer": "✦",
    "analyst": "◎",
    "validator": "✓",
    "orchestrator": "⬢",
}


def esc(text: str) -> str:
    return html.escape(text)


def class_label(agent_class: str) -> str:
    return CLASS_LABELS.get(agent_class, agent_class)


def class_icon(agent_class: str) -> str:
    return CLASS_ICONS.get(agent_class, "●")


def risk_label(level: str) -> str:
    return {"düşük": "Düşük", "orta": "Orta", "yüksek": "Yüksek"}.get(level, level)


def format_num(n: int | float) -> str:
    n = float(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return f"{n:.0f}" if n == int(n) else f"{n:.1f}"


def capabilities_list(manifest: Optional[AgentManifest]) -> str:
    if not manifest or not manifest.capabilities:
        return ""
    return "".join(
        f'<li><span class="cap-name">{esc(c.name)}</span> {esc(c.description)}</li>'
        for c in manifest.capabilities
    )
