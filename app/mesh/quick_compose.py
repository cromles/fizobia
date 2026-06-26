"""Hızlı metin — tek LLM çağrısı (şiir, makale, serbest istem)."""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List

from app.mesh.agent_dialogue import get_dialogue_bus
from app.mesh.founders import ORCHESTRATOR_ID
from app.mesh.mission import pipeline_mission_opener
from app.workers.media_story import AGENT_ID as STORY_ID, DISPLAY_NAME as STORY_NAME


async def run_quick_compose(*, user_prompt: str) -> Dict[str, Any]:
    """Şiir / metin istekleri — 1 ajan, 1 API, ~2 sn."""
    dialogue = get_dialogue_bus()
    job_id = f"compose_{uuid.uuid4().hex[:10]}"
    thread_id = f"compose_{job_id}"
    started = time.perf_counter()
    synapse_log: List[str] = []

    def log(line: str) -> None:
        synapse_log.append(line)

    pipeline_mission_opener(thread_id)
    log("[Orkestratör] Hızlı metin modu — tek Story-Weaver, arena yok.")
    dialogue.broadcast(
        ORCHESTRATOR_ID,
        f"Hızlı üretim: {user_prompt[:80]}…",
        intent="compose_start",
        thread_id=thread_id,
    )

    from app.config import settings

    text = ""
    source = "template"
    llm_meta: Dict[str, Any] = {}

    if settings.llm_enabled:
        try:
            from app.llm.client import chat_completion

            system = (
                "Sen Axium yazı departmanındaki Story-Weaver ajanısın. "
                "Kullanıcının istediği metni Türkçe, akıcı ve özgün yaz. "
                "Sadece istenen metni döndür — açıklama ekleme."
            )
            t0 = time.perf_counter()
            text, llm_meta = await chat_completion(
                system=system,
                user=user_prompt,
                temperature=0.9,
                max_tokens=400,
                timeout=35.0,
            )
            ms = round((time.perf_counter() - t0) * 1000, 1)
            source = "llm"
            log(f"[{STORY_NAME}] Gemini üretti · {len(text.split())} kelime · {ms}ms")
        except Exception as exc:
            log(f"[{STORY_NAME}] LLM hatası — şablon: {exc}")
            text = _template_compose(user_prompt)
            source = "template_fallback"
    else:
        text = _template_compose(user_prompt)
        log(f"[{STORY_NAME}] Şablon modu · {len(text.split())} kelime")

    dialogue.say(
        ORCHESTRATOR_ID,
        STORY_ID,
        "Metin hazır — hızlı yol tamamlandı.",
        intent="compose_done",
        thread_id=thread_id,
    )

    total_ms = round((time.perf_counter() - started) * 1000, 1)
    return {
        "job_id": job_id,
        "mode": "quick_compose",
        "user_prompt": user_prompt,
        "synapse_log": synapse_log,
        "winner": {
            "agent_id": STORY_ID,
            "display_name": STORY_NAME,
            "script": text,
            "critic_score": 1.0,
        },
        "render": {
            "format": "text",
            "status": "ready",
            "text": text,
            "source": source,
            "llm_meta": llm_meta or None,
        },
        "total_latency_ms": total_ms,
        "dialogue_thread": thread_id,
        "dialogue_messages": len(dialogue.list_messages(thread_id=thread_id)),
        "message": f"Metin hazır — {STORY_NAME} ({source})",
        "real_data": source == "llm",
    }


def _template_compose(prompt: str) -> str:
    p = prompt.lower()
    if "şiir" in p or "siir" in p or "poem" in p:
        return (
            "Gözlerin deniz, sesin rüzgar,\n"
            "Kalbimde bir iz, silinmez yar.\n"
            "Aşk dediğin bu mu, bilmem ki,\n"
            "Sen varsın hayatta, gerisi hiç."
        )
    return f"İstemin üzerine kısa metin:\n\n{prompt[:200]}\n\n— Axium Story-Weaver"
