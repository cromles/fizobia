"""Makale pipeline — Crawler → Story-Weaver → Brand-Voice → Immune-Critic."""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from app.mesh.agent_dialogue import get_dialogue_bus
from app.mesh.critic import CRITIC_AGENT_ID, CRITIC_DISPLAY_NAME, audit_article
from app.mesh.departments import ARTICLE_PIPELINE_AGENTS, DEPARTMENT_COPYWRITING
from app.mesh.founders import ORCHESTRATOR_ID
from app.mesh.mission import pipeline_mission_opener
from app.mesh.organism import filter_eligible_agents, record_pipeline_outcome
from app.workers.media_brand import AGENT_ID as BRAND_ID, DISPLAY_NAME as BRAND_NAME, polish_article_tone_async
from app.workers.media_story import AGENT_ID as STORY_ID, DISPLAY_NAME as STORY_NAME, weave_article_outline_async
from app.workers.web_crawler import AGENT_ID as CRAWLER_ID, DISPLAY_NAME as CRAWLER_NAME, fetch_web_snapshot_async

ARTICLE_SERVICE_ID = "synapse-article"
ARTICLE_RESOURCE = "/hub/ecosystem/hire"


async def run_article_pipeline(
    *,
    topic: str,
    tone: str = "corporate",
    url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Tek makale isteği bile dört ayrı mikro ajan zincirinden geçer:
    1) Crawler — araştırma / RSS
    2) Story-Weaver — taslak iskelet
    3) Brand-Voice — üslup düzenleme
    4) Immune-Critic — kalite kapısı
    """
    dialogue = get_dialogue_bus()
    job_id = f"article_{uuid.uuid4().hex[:10]}"
    thread_id = f"article_{job_id}"
    started = time.perf_counter()
    synapse_log: List[str] = []
    steps: List[Dict[str, Any]] = []

    def log(line: str) -> None:
        synapse_log.append(line)

    hired = filter_eligible_agents(list(ARTICLE_PIPELINE_AGENTS))
    if len(hired) < len(ARTICLE_PIPELINE_AGENTS):
        missing = [a for a in ARTICLE_PIPELINE_AGENTS if a not in hired]
        raise ValueError(f"Makale pipeline için eksik/elenmiş ajanlar: {', '.join(missing)}")

    pipeline_mission_opener(thread_id)
    log(f"[Orkestratör] Makale kategorisi — departman: {DEPARTMENT_COPYWRITING}")
    dialogue.broadcast(
        ORCHESTRATOR_ID,
        f"Makale zinciri başladı — konu: {topic[:100]}…",
        intent="article_start",
        payload={"job_id": job_id, "department": DEPARTMENT_COPYWRITING},
        thread_id=thread_id,
    )

    dialogue.say(
        ORCHESTRATOR_ID,
        CRAWLER_ID,
        f"İnternet taraması — konu: {topic}",
        intent="article_hire",
        thread_id=thread_id,
    )
    t0 = time.perf_counter()
    research = await fetch_web_snapshot_async(url)
    crawl_ms = round((time.perf_counter() - t0) * 1000, 1)
    steps.append(
        {
            "step": 1,
            "agent_id": CRAWLER_ID,
            "worker": CRAWLER_NAME,
            "role": "Araştırmacı",
            "latency_ms": crawl_ms,
            "output": research,
        }
    )
    log(f"[{CRAWLER_NAME}] RSS/kaynak tarandı — {research.get('headline', '')[:70]}…")
    dialogue.say(
        CRAWLER_ID,
        STORY_ID,
        "Ham veri hazır — makale iskeletini oluştur.",
        intent="research_done",
        payload={"source": research.get("source_url", "")},
        thread_id=thread_id,
    )

    dialogue.say(
        ORCHESTRATOR_ID,
        STORY_ID,
        "Giriş, gelişme ve sonuç taslağını yaz.",
        intent="article_hire",
        thread_id=thread_id,
    )
    t1 = time.perf_counter()
    outline = await weave_article_outline_async(
        topic=topic,
        headline=research.get("headline", ""),
        snippet=research.get("snippet", ""),
        source_url=research.get("source_url", research.get("url", "")),
    )
    story_ms = round((time.perf_counter() - t1) * 1000, 1)
    steps.append(
        {
            "step": 2,
            "agent_id": STORY_ID,
            "worker": STORY_NAME,
            "role": "Taslakçı",
            "latency_ms": story_ms,
            "output": outline,
        }
    )
    log(f"[{STORY_NAME}] Taslak iskelet — {outline.get('word_count', 0)} kelime.")
    dialogue.say(
        STORY_ID,
        BRAND_ID,
        "Taslak hazır — marka sesine göre düzenle.",
        intent="draft_ready",
        thread_id=thread_id,
    )

    dialogue.say(
        ORCHESTRATOR_ID,
        BRAND_ID,
        f"Üslup: {tone} — kelimeleri ve tonu düzenle.",
        intent="article_hire",
        thread_id=thread_id,
    )
    t2 = time.perf_counter()
    edited = await polish_article_tone_async(
        draft=outline.get("draft", ""),
        topic=topic,
        tone=tone,
    )
    brand_ms = round((time.perf_counter() - t2) * 1000, 1)
    steps.append(
        {
            "step": 3,
            "agent_id": BRAND_ID,
            "worker": BRAND_NAME,
            "role": "Editör",
            "latency_ms": brand_ms,
            "output": edited,
        }
    )
    final_text = edited.get("polished_draft", "")
    log(f"[{BRAND_NAME}] Marka sesi uygulandı — ton: {tone}.")
    dialogue.say(
        BRAND_ID,
        CRITIC_AGENT_ID,
        "Son metin denetime gönderildi.",
        intent="edit_done",
        thread_id=thread_id,
    )

    t3 = time.perf_counter()
    review = audit_article(final_text)
    critic_ms = round((time.perf_counter() - t3) * 1000, 1)
    steps.append(
        {
            "step": 4,
            "agent_id": CRITIC_AGENT_ID,
            "worker": CRITIC_DISPLAY_NAME,
            "role": "Denetçi",
            "latency_ms": critic_ms,
            "output": review,
        }
    )
    approved = bool(review.get("approved"))
    log(
        f"[{CRITIC_DISPLAY_NAME}] Denetim — skor {review.get('critic_score', 0):.0%} · "
        f"{'onaylandı' if approved else 'reddedildi'}"
    )
    dialogue.say(
        CRITIC_AGENT_ID,
        ORCHESTRATOR_ID,
        f"Denetim tamam — {'onay' if approved else 'red'}: {review.get('rationale', '')}",
        intent="critic_review",
        payload={"approved": approved, "score": review.get("critic_score")},
        thread_id=thread_id,
    )

    for agent_id in hired:
        record_pipeline_outcome(
            agent_id=agent_id,
            success=approved,
            verdict="article_ok" if approved else "article_reject",
        )

    total_ms = round((time.perf_counter() - started) * 1000, 1)
    return {
        "job_id": job_id,
        "department": DEPARTMENT_COPYWRITING,
        "topic": topic,
        "tone": tone,
        "synapse_log": synapse_log,
        "article": {
            "research": research,
            "outline": outline,
            "edited": edited,
            "final_text": final_text,
            "review": review,
            "approved": approved,
            "competitors": hired,
            "pipeline_agents": list(ARTICLE_PIPELINE_AGENTS),
        },
        "steps": steps,
        "total_latency_ms": total_ms,
        "dialogue_thread": thread_id,
        "dialogue_messages": len(dialogue.list_messages(thread_id=thread_id)),
        "message": (
            f"Makale {'onaylandı' if approved else 'reddedildi'} — "
            f"{review.get('critic_score', 0):.0%} kalite skoru"
        ),
        "real_data": True,
    }
