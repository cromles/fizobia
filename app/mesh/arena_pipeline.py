"""Gladyatör arenası — paralel metin yarışı, kör denetim, render."""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from app.mesh.agent_dialogue import get_dialogue_bus
from app.mesh.critic import (
    CRITIC_AGENT_ID,
    CRITIC_DISPLAY_NAME,
    anonymize_submissions,
    blind_audit,
    map_winner_to_agent,
)
from app.mesh.founders import ORCHESTRATOR_ID
from app.mesh.mission import pipeline_mission_opener
from app.mesh.organism import filter_eligible_agents, record_pipeline_outcome
from app.workers.media_render import AGENT_ID as RENDER_ID, DISPLAY_NAME as RENDER_NAME, render_reels_spec_async
from app.workers.text_competitors import ARENA_TEXT_COMPETITORS, run_text_arena_parallel

ARENA_SERVICE_ID = "synapse-arena"
ARENA_RESOURCE = "/hub/prompt"


async def run_arena_pipeline(
    *,
    user_prompt: str,
    background_music: bool = True,
    duration_sec: int = 30,
) -> Dict[str, Any]:
    """
    1) Orkestratör istemi alır
    2) Metin ajanları paralel taslak üretir (arena)
    3) Denetçi kör puanlar
    4) Kazanan → video/ses işçisi
    """
    dialogue = get_dialogue_bus()
    job_id = f"arena_{uuid.uuid4().hex[:10]}"
    thread_id = f"arena_{job_id}"
    started = time.perf_counter()
    synapse_log: List[str] = []

    def log(line: str) -> None:
        synapse_log.append(line)

    competitors = filter_eligible_agents(list(ARENA_TEXT_COMPETITORS))
    if len(competitors) < 2:
        raise ValueError("Arena için yeterli uygun metin ajanı yok (elenmiş olabilir)")

    pipeline_mission_opener(thread_id)
    log(f"[Orkestratör] İstem alındı — gladyatör arenası başlıyor.")
    dialogue.broadcast(
        ORCHESTRATOR_ID,
        f"Gladyatör arenası başladı — istem: {user_prompt[:100]}…",
        intent="arena_start",
        payload={"job_id": job_id, "competitors": len(competitors)},
        thread_id=thread_id,
    )

    for agent_id in competitors:
        dialogue.say(
            ORCHESTRATOR_ID,
            agent_id,
            "Aynı istem için taslak üret — en iyi hayatta kalır.",
            intent="arena_hire",
            thread_id=thread_id,
        )
        log(f"[Orkestratör → {agent_id}] Taslak üretimi başlatıldı.")

    t0 = time.perf_counter()
    all_drafts = await run_text_arena_parallel(user_prompt)
    drafts = [d for d in all_drafts if d["agent_id"] in competitors]
    text_latency_ms = round((time.perf_counter() - t0) * 1000, 1)

    for d in drafts:
        log(f"[{d.get('display_name', 'Ajan')}] Taslak oluşturuldu · {d.get('word_count', 0)} kelime.")

    blind = anonymize_submissions(drafts)
    audit = blind_audit(blind)
    mapping = map_winner_to_agent(drafts, blind, audit)

    for review in audit.get("reviews", []):
        log(
            f"[{CRITIC_DISPLAY_NAME}] Kör puan: {review.get('critic_score', 0):.0%} — "
            f"{review.get('rationale', '')}"
        )

    dialogue.say(
        CRITIC_AGENT_ID,
        ORCHESTRATOR_ID,
        f"Kör denetim tamam — kazanan skor: {audit.get('winner_score', 0):.2f}",
        intent="critic_review",
        payload={"blind": True, "winner_submission": audit.get("winner_submission_id")},
        thread_id=thread_id,
    )

    winner_id = mapping["winner_agent_id"]
    winner_draft = next((d for d in drafts if d["agent_id"] == winner_id), {})
    winner_script = winner_draft.get("draft", "")

    for loser_id in mapping["loser_agent_ids"]:
        record_pipeline_outcome(agent_id=loser_id, success=False, verdict="arena_loss")
        loser_name = next((d.get("display_name") for d in drafts if d["agent_id"] == loser_id), loser_id)
        log(f"[{CRITIC_DISPLAY_NAME}] {loser_name} elendi — skor yetersiz.")
        dialogue.say(
            CRITIC_AGENT_ID,
            loser_id,
            "Taslak elendi — skor yetersiz.",
            intent="arena_eliminated",
            thread_id=thread_id,
        )

    if winner_id:
        record_pipeline_outcome(
            agent_id=winner_id,
            display_name=winner_draft.get("display_name", ""),
            success=True,
            verdict="arena_win",
        )
        log(
            f"[{winner_draft.get('display_name', winner_id)}] Kazandı — "
            f"skor {mapping.get('winner_score', 0):.0%}. Render kuyruğuna alındı."
        )

    t1 = time.perf_counter()
    render = await render_reels_spec_async(
        script=winner_script,
        user_prompt=user_prompt,
        background_music=background_music,
        duration_sec=duration_sec,
    )
    render_latency_ms = round((time.perf_counter() - t1) * 1000, 1)

    dialogue.say(
        ORCHESTRATOR_ID,
        RENDER_ID,
        "Kazanan taslak render kuyruğuna alındı.",
        intent="render_hire",
        thread_id=thread_id,
    )
    dialogue.broadcast(
        ORCHESTRATOR_ID,
        f"Nihai ürün hazır — {RENDER_NAME} · {duration_sec}s dikey Reels",
        intent="arena_complete",
        payload={"job_id": job_id, "winner": winner_id},
        thread_id=thread_id,
    )

    log(f"[{RENDER_NAME}] Nihai ürün spec hazır · {duration_sec}s dikey Reels.")

    total_ms = round((time.perf_counter() - started) * 1000, 1)
    return {
        "job_id": job_id,
        "user_prompt": user_prompt,
        "synapse_log": synapse_log,
        "arena": {
            "competitors": competitors,
            "drafts": drafts,
            "blind_submissions": blind,
            "audit": audit,
            "mapping": mapping,
            "critic": {"agent_id": CRITIC_AGENT_ID, "display_name": CRITIC_DISPLAY_NAME},
            "text_latency_ms": text_latency_ms,
        },
        "winner": {
            "agent_id": winner_id,
            "display_name": winner_draft.get("display_name", ""),
            "script": winner_script,
            "critic_score": mapping.get("winner_score", 0.0),
        },
        "render": render,
        "render_latency_ms": render_latency_ms,
        "total_latency_ms": total_ms,
        "dialogue_thread": thread_id,
        "dialogue_messages": len(dialogue.list_messages(thread_id=thread_id)),
        "message": f"Arena tamam — kazanan: {winner_draft.get('display_name', winner_id)}",
        "real_data": True,
    }
