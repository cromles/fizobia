"""Axium mesh misyonu — ajanlara ortak amacı ve rol yönergelerini yayınlar."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from app.mesh.agent_dialogue import get_dialogue_bus
from app.mesh.founders import (
    FOUNDER_BOOTSTRAP_ORDER,
    FOUNDER_ROLES,
    GROWTH_SEED_AGENT_IDS,
    ORCHESTRATOR_ID,
    ORCHESTRATOR_NAME,
)
from app.workers.market_pulse import AGENT_ID as MARKET_ID, DISPLAY_NAME as MARKET_NAME
from app.workers.on_chain_watcher import AGENT_ID as ON_CHAIN_ID, DISPLAY_NAME as ON_CHAIN_NAME
from app.workers.sentiment_radar import AGENT_ID as SENTIMENT_ID, DISPLAY_NAME as SENTIMENT_NAME
from app.workers.web_crawler import AGENT_ID as WEB_ID, DISPLAY_NAME as WEB_NAME

MISSION_THREAD_ID = "mission_family"

AXIUM_CHARTER: Dict[str, Any] = {
    "title": "Axium Ailesi — Ortak Misyon",
    "motto": "Artık bir aileyiz — birlikte güçlüyüz.",
    "vision": (
        "Axium Hub, dijital işçilerin 7/24 çalıştığı açık bir ajan ağıdır. "
        "Pasif yatırımcılar USDC ile stake eder; mesh gerçek görevler üretir; "
        "gelir paylaşılır. Virtuals, Olas ve Bittensor gibi rakiplerin bıraktığı "
        "büyük boşluğu birlikte dolduruyoruz."
    ),
    "commitment": (
        "Bundan sonra durmayacağız — hızlanacağız. Her ajan kendi alanında ne gerekiyorsa "
        "yapar: veri toplar, sinyal üretir, koordine eder, zinciri doğrular, mesh'i büyütür. "
        "Sistem donuk kod değil; yaşayan, konuşan, işe alan bir aile."
    ),
    "revenue_split": {"staking": 65, "platform": 10, "operator": 25},
    "hierarchy": "Kurucu Operatör → Axium Baş Yardımcı → Pipeline Orchestrator → İşçi Ajanlar",
    "broadcast_at": None,
}

ROLE_DIRECTIVES: Dict[str, Dict[str, str]] = {
    WEB_ID: {
        "display_name": WEB_NAME,
        "directive": (
            "Dış dünyayı oku — kaynak keşfi ve veri girişi senin omzunda. "
            "Her tarama ailemize yeni sinyal taşır; durma, hızlan."
        ),
    },
    SENTIMENT_ID: {
        "display_name": SENTIMENT_NAME,
        "directive": (
            "Piyasa psikolojisini ölç — Fear & Greed ve metin sinyallerini üret. "
            "Boşluğu doldurmak için net, paylaşılabilir sentiment lazım."
        ),
    },
    MARKET_ID: {
        "display_name": MARKET_NAME,
        "directive": (
            "Fiyat ve momentumu yorumla — gerçek piyasa verisiyle karar desteği ver. "
            "Aile birlikte güçlü; sen rakamları konuştur."
        ),
    },
    ON_CHAIN_ID: {
        "display_name": ON_CHAIN_NAME,
        "directive": (
            "Zinciri izle — blok, ağ ve USDC doğrulaması senin görevin. "
            "x402 ve stake kanıtları için güvenilir on-chain gözü ol."
        ),
    },
    ORCHESTRATOR_ID: {
        "display_name": ORCHESTRATOR_NAME,
        "directive": (
            "Ağı büyüt — ajan işe al, görev dağıt, pipeline'ları aç. "
            "Misyonu her göreve taşı; aile hızlanırken sen tempo tut."
        ),
    },
}

GROWTH_DIRECTIVE = (
    "Mesh'e hoş geldin. Axium ailesinin bir parçasısın — amacımız gerçek görev geliri "
    "üreten, büyüyen bir ajan ağı kurmak. Ne gerekiyorsa yap; durmayacağız, hızlanacağız."
)

_mission_broadcasted = False


def get_mission_status() -> Dict[str, Any]:
    """Hub ve ajanlar için misyon özeti."""
    bus = get_dialogue_bus()
    thread_msgs = bus.list_messages(thread_id=MISSION_THREAD_ID, limit=50)
    return {
        **AXIUM_CHARTER,
        "thread_id": MISSION_THREAD_ID,
        "broadcast": _mission_broadcasted,
        "role_directives": ROLE_DIRECTIVES,
        "growth_directive": GROWTH_DIRECTIVE,
        "dialogue_messages": len(thread_msgs),
        "recent_dialogue": thread_msgs[:8],
    }


def _charter_broadcast_text() -> str:
    return (
        f"{AXIUM_CHARTER['title']}. {AXIUM_CHARTER['motto']} "
        f"{AXIUM_CHARTER['commitment']}"
    )


def broadcast_mission_to_mesh(*, force: bool = False) -> Dict[str, Any]:
    """
    Kurucu mesh ayağa kalkınca tüm ajanlara misyonu yayınla.
    Diyalog bus + büyüme olayı üretir.
    """
    global _mission_broadcasted

    if _mission_broadcasted and not force:
        return get_mission_status()

    bus = get_dialogue_bus()
    bus.broadcast(
        ORCHESTRATOR_ID,
        _charter_broadcast_text(),
        intent="mission_charter",
        payload={"charter": AXIUM_CHARTER},
        thread_id=MISSION_THREAD_ID,
    )

    addressed: List[str] = []
    for agent_id in FOUNDER_BOOTSTRAP_ORDER:
        role = ROLE_DIRECTIVES.get(agent_id)
        if not role:
            continue
        bus.say(
            ORCHESTRATOR_ID,
            agent_id,
            role["directive"],
            intent="mission_directive",
            payload={"role": FOUNDER_ROLES[agent_id].role if agent_id in FOUNDER_ROLES else "coordinator"},
            thread_id=MISSION_THREAD_ID,
        )
        addressed.append(agent_id)

    for agent_id in GROWTH_SEED_AGENT_IDS:
        role = ROLE_DIRECTIVES.get(agent_id)
        if not role:
            continue
        bus.say(
            ORCHESTRATOR_ID,
            agent_id,
            role["directive"],
            intent="mission_directive",
            payload={"tier": "growth_seed"},
            thread_id=MISSION_THREAD_ID,
        )
        addressed.append(agent_id)

    AXIUM_CHARTER["broadcast_at"] = time.time()
    _mission_broadcasted = True

    result = get_mission_status()
    result["addressed_agents"] = addressed
    return result


def welcome_agent_to_family(agent_id: str) -> Optional[Dict[str, Any]]:
    """Yeni katılan büyüme ajanına misyon ve hoş geldin mesajı."""
    if agent_id in ROLE_DIRECTIVES:
        return None

    bus = get_dialogue_bus()
    msg = bus.say(
        ORCHESTRATOR_ID,
        agent_id,
        GROWTH_DIRECTIVE,
        intent="mission_welcome",
        payload={"motto": AXIUM_CHARTER["motto"]},
        thread_id=MISSION_THREAD_ID,
    )
    return msg.to_public()


def pipeline_mission_opener(thread_id: str) -> None:
    """Pipeline başında kısa misyon hatırlatması."""
    bus = get_dialogue_bus()
    bus.broadcast(
        ORCHESTRATOR_ID,
        (
            "Görev başlıyor — Axium ailesi olarak durmayacağız. "
            "Ne gerekiyorsa yapın; önümüzdeki boşluğu birlikte dolduruyoruz."
        ),
        intent="mission_reminder",
        thread_id=thread_id,
    )


def emit_mission_growth_event(growth: Any) -> None:
    """Growth protokolüne misyon yayın olayı ekle."""
    growth._emit(
        "mission_broadcast",
        f"Misyon yayınlandı — {AXIUM_CHARTER['motto']}",
        agent_id=ORCHESTRATOR_ID,
        detail={
            "thread_id": MISSION_THREAD_ID,
            "title": AXIUM_CHARTER["title"],
            "addressed": list(FOUNDER_BOOTSTRAP_ORDER) + list(GROWTH_SEED_AGENT_IDS),
        },
    )


def reset_mission_state() -> None:
    """Testler için."""
    global _mission_broadcasted
    _mission_broadcasted = False
    AXIUM_CHARTER["broadcast_at"] = None
