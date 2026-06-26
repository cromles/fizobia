"""Uzman metin pipeline — şiir / düzyazı (arena değil)."""

from __future__ import annotations

import re
import time
import uuid
from typing import Any, Dict, List, Tuple

from app.mesh.agent_dialogue import get_dialogue_bus
from app.mesh.founders import ORCHESTRATOR_ID
from app.mesh.mission import pipeline_mission_opener
from app.mesh.prompt_intent import compose_kind
from app.workers.media_brand import AGENT_ID as BRAND_ID, DISPLAY_NAME as BRAND_NAME
from app.workers.media_story import AGENT_ID as STORY_ID, DISPLAY_NAME as STORY_NAME
from app.mesh.critic import CRITIC_AGENT_ID, CRITIC_DISPLAY_NAME

_MIN_POEM_LINES = 8
_MIN_POEM_WORDS = 60
_MIN_PROSE_WORDS = 100


async def run_quick_compose(*, user_prompt: str) -> Dict[str, Any]:
    """Şiir ve metin — Lyric/Story-Weaver → Brand-Voice → kalite kapısı."""
    dialogue = get_dialogue_bus()
    job_id = f"compose_{uuid.uuid4().hex[:10]}"
    thread_id = f"compose_{job_id}"
    started = time.perf_counter()
    synapse_log: List[str] = []
    kind = compose_kind(user_prompt)

    def log(line: str) -> None:
        synapse_log.append(line)

    pipeline_mission_opener(thread_id)
    log(f"[Orkestratör] Uzman metin modu — tür: {kind} (arena kapalı).")
    dialogue.broadcast(
        ORCHESTRATOR_ID,
        f"Uzman yazı departmanı — {kind}: {user_prompt[:70]}…",
        intent="compose_start",
        thread_id=thread_id,
    )

    from app.config import settings

    text = ""
    source = "template"
    steps: List[Dict[str, Any]] = []

    if settings.llm_enabled:
        try:
            text, source, steps = await _llm_compose_chain(user_prompt, kind=kind, log=log, dialogue=dialogue, thread_id=thread_id)
        except Exception as exc:
            log(f"[{STORY_NAME}] Zincir hatası — şablon: {exc}")
            text = _template_compose(user_prompt, kind=kind)
            source = "template_fallback"
    else:
        text = _template_compose(user_prompt, kind=kind)
        log(f"[{STORY_NAME}] Şablon · {len(text.split())} kelime")

    wc = len(text.split())
    lines = len([ln for ln in text.splitlines() if ln.strip()])
    approved = _quality_ok(text, kind=kind)

    log(
        f"[{CRITIC_DISPLAY_NAME}] Kalite — {wc} kelime, {lines} satır · "
        f"{'onay' if approved else 'düşük skor ama en iyi üretim'}"
    )
    dialogue.say(
        CRITIC_AGENT_ID,
        ORCHESTRATOR_ID,
        f"Metin denetimi — {wc} kelime",
        intent="compose_audit",
        thread_id=thread_id,
    )

    total_ms = round((time.perf_counter() - started) * 1000, 1)
    return {
        "job_id": job_id,
        "mode": "quick_compose",
        "compose_kind": kind,
        "user_prompt": user_prompt,
        "synapse_log": synapse_log,
        "steps": steps,
        "winner": {
            "agent_id": STORY_ID,
            "display_name": "Lyric-Weaver" if kind == "poem" else STORY_NAME,
            "script": text,
            "critic_score": 0.92 if approved else 0.65,
        },
        "render": {
            "format": "poem" if kind == "poem" else "text",
            "status": "ready",
            "text": text,
            "source": source,
            "word_count": wc,
            "line_count": lines,
        },
        "total_latency_ms": total_ms,
        "dialogue_thread": thread_id,
        "dialogue_messages": len(dialogue.list_messages(thread_id=thread_id)),
        "message": f"{'Şiir' if kind == 'poem' else 'Metin'} hazır — {wc} kelime ({source})",
        "real_data": source.startswith("llm"),
    }


async def _llm_compose_chain(
    user_prompt: str,
    *,
    kind: str,
    log,
    dialogue,
    thread_id: str,
) -> Tuple[str, str, List[Dict[str, Any]]]:
    from app.llm.client import chat_completion
    from app.llm.prompts import BRAND_TONE_SYSTEM, LYRIC_WEAVER_SYSTEM, PROSE_WEAVER_SYSTEM

    steps: List[Dict[str, Any]] = []

    if kind == "poem":
        system = LYRIC_WEAVER_SYSTEM
        tone = "lyrical"
        max_tok = 700
    else:
        system = PROSE_WEAVER_SYSTEM
        tone = "corporate"
        max_tok = 900

    log(f"[Lyric-Weaver] Taslak üretiliyor…")
    dialogue.say(ORCHESTRATOR_ID, STORY_ID, "Şiir/metin taslağı iste", intent="compose_draft", thread_id=thread_id)
    t0 = time.perf_counter()
    draft, m1 = await chat_completion(
        system=system,
        user=user_prompt,
        temperature=0.88,
        max_tokens=max_tok,
        timeout=40.0,
    )
    steps.append({"agent": STORY_NAME, "latency_ms": m1.get("latency_ms"), "words": len(draft.split())})

    if kind == "poem" and len(draft.split()) < _MIN_POEM_WORDS:
        log(f"[Lyric-Weaver] Kısa taslak — genişletme turu")
        draft, m1b = await chat_completion(
            system=system + " ÖNCEKİ TASLAK ÇOK KISA. En az 12 satır ve 80 kelime yaz.",
            user=f"İstem: {user_prompt}\n\nÖnceki (kısa) taslak:\n{draft}\n\nŞimdi tam şiiri yaz.",
            temperature=0.9,
            max_tokens=max_tok,
        )
        steps.append({"agent": STORY_NAME, "step": "expand", "words": len(draft.split())})

    log(f"[{BRAND_NAME}] Üslup düzenlemesi ({tone})…")
    t1 = time.perf_counter()
    polished, m2 = await chat_completion(
        system=BRAND_TONE_SYSTEM.get(tone, BRAND_TONE_SYSTEM["lyrical"]),
        user=f"Konu/istem: {user_prompt}\n\nDüzenle:\n{draft}",
        temperature=0.75,
        max_tokens=max_tok,
    )
    steps.append({"agent": BRAND_NAME, "latency_ms": round((time.perf_counter() - t1) * 1000, 1)})

    final = polished.strip() or draft.strip()
    log(f"[Lyric-Weaver → {BRAND_NAME}] Tamam · {len(final.split())} kelime")
    return final, "llm", steps


def _quality_ok(text: str, *, kind: str) -> bool:
    wc = len(text.split())
    lines = len([ln for ln in text.splitlines() if ln.strip()])
    if kind == "poem":
        return wc >= _MIN_POEM_WORDS and lines >= _MIN_POEM_LINES
    return wc >= _MIN_PROSE_WORDS


def _template_compose(prompt: str, *, kind: str = "poem") -> str:
    if kind == "poem" or re.search(r"şiir|siir|poem|aşk", prompt, re.I):
        return (
            "Gözlerin deniz, içimde dalga dalga,\n"
            "Adını fısıldar rüzgâr, geceye karışa.\n"
            "Ellerin uzak, kalbim yakın sana,\n"
            "Bu aşk bir ateş mi, yoksa serap mı?\n\n"
            "Hatıraların sokak lambası gibi,\n"
            "Aydınlatır karanlık köşelerimi.\n"
            "Sen gelmesen de, beklerim yine,\n"
            "Çünkü sensiz geçen her an eksik.\n\n"
            "Belki yarın, belki başka bir ömürde,\n"
            "Kavuşuruz hayalin en güzel yerinde.\n"
            "Şimdilik bu dizeler kalsın sana,\n"
            "İmzası: Axium Lyric-Weaver."
        )
    return (
        f"{prompt.strip()}\n\n"
        "Bu metin Axium Story-Weaver tarafından hazırlandı. "
        "LLM anahtarı aktif olduğunda çok daha zengin içerik üretilir."
    )
