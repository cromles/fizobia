"""Ekosistem birleştirme — mesh proof + medya dalgası + sermaye radarı."""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List, Optional

from app.mesh.agent_dialogue import get_dialogue_bus
from app.mesh.ecosystem_registry import ECOSYSTEM_ASSEMBLY_AGENTS
from app.mesh.founders import ORCHESTRATOR_ID
from app.mesh.mission import pipeline_mission_opener
from app.mesh.proof_pipeline import run_mesh_proof_pipeline
from app.workers.capital_fundraise import (
    AGENT_ID as CAPITAL_ID,
    DISPLAY_NAME as CAPITAL_NAME,
    scan_fundraise_signals_async,
)
from app.workers.media_brand import (
    AGENT_ID as BRAND_ID,
    DISPLAY_NAME as BRAND_NAME,
    craft_brand_copy_async,
)
from app.workers.media_outreach import (
    AGENT_ID as OUTREACH_ID,
    DISPLAY_NAME as OUTREACH_NAME,
    build_outreach_pitch_async,
)
from app.workers.media_proof import (
    AGENT_ID as PROOF_MEDIA_ID,
    DISPLAY_NAME as PROOF_MEDIA_NAME,
    format_proof_share_async,
)
from app.workers.media_story import (
    AGENT_ID as STORY_ID,
    DISPLAY_NAME as STORY_NAME,
    weave_story_async,
)

ASSEMBLY_SERVICE_ID = "ecosystem-assembly"
ASSEMBLY_RESOURCE = "/hub/ecosystem/assemble"


async def run_ecosystem_assembly(
    *,
    symbol: str = "bitcoin",
    url: Optional[str] = None,
    skip_mesh_proof: bool = False,
    hub_stats: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Tam ekosistem birleştirme:
    mesh proof → story → brand → outreach → proof share → fund radar
    """
    dialogue = get_dialogue_bus()
    thread_id = f"assembly_{uuid.uuid4().hex[:8]}"
    started = time.perf_counter()
    steps: List[Dict[str, Any]] = []

    pipeline_mission_opener(thread_id)
    dialogue.say(
        ORCHESTRATOR_ID,
        STORY_ID,
        f"Ekosistem birleştirme başlıyor — {symbol}. Önce mesh kanıtı, sonra medya dalgası.",
        intent="assembly_start",
        thread_id=thread_id,
    )

    if skip_mesh_proof:
        proof = {
            "proof_id": f"proof_skip_{uuid.uuid4().hex[:6]}",
            "verdict": "neutral",
            "total_latency_ms": 0,
            "steps": [],
            "dialogue_thread": thread_id,
        }
    else:
        proof = await run_mesh_proof_pipeline(symbol=symbol, url=url)

    proof_steps = proof.get("steps", [])
    web_out = proof_steps[0]["output"] if len(proof_steps) > 0 else {}
    sent_out = proof_steps[1]["output"] if len(proof_steps) > 1 else {}
    mkt_out = proof_steps[2]["output"] if len(proof_steps) > 2 else {}

    t0 = time.perf_counter()
    story = await weave_story_async(
        symbol=symbol,
        verdict=proof.get("verdict", ""),
        headline=web_out.get("headline", ""),
        sentiment=sent_out.get("sentiment", ""),
        price_usd=mkt_out.get("price_usd"),
        proof_id=proof.get("proof_id", ""),
    )
    steps.append(
        {
            "step": len(steps) + 1,
            "agent_id": STORY_ID,
            "worker": STORY_NAME,
            "capability": "story_weaver",
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
            "output": story,
        }
    )
    dialogue.say(
        STORY_ID,
        BRAND_ID,
        f"Hikaye hazır: {story['headline']}",
        intent="handoff",
        thread_id=thread_id,
    )

    t0 = time.perf_counter()
    brand = await craft_brand_copy_async(narrative=story.get("narrative", ""), symbol=symbol)
    steps.append(
        {
            "step": len(steps) + 1,
            "agent_id": BRAND_ID,
            "worker": BRAND_NAME,
            "capability": "brand_voice",
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
            "output": brand,
        }
    )
    dialogue.say(BRAND_ID, OUTREACH_ID, "Marka metni hazır — pitch üret", intent="handoff", thread_id=thread_id)

    t0 = time.perf_counter()
    outreach = await build_outreach_pitch_async(
        tagline=brand.get("tagline", ""),
        symbol=symbol,
        proof_id=proof.get("proof_id", ""),
    )
    steps.append(
        {
            "step": len(steps) + 1,
            "agent_id": OUTREACH_ID,
            "worker": OUTREACH_NAME,
            "capability": "outreach",
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
            "output": outreach,
        }
    )
    dialogue.say(
        OUTREACH_ID,
        PROOF_MEDIA_ID,
        "Pitch hazır — kanıt kartını yayınla",
        intent="handoff",
        thread_id=thread_id,
    )

    t0 = time.perf_counter()
    share = await format_proof_share_async(
        proof_id=proof.get("proof_id", ""),
        verdict=proof.get("verdict", ""),
        narrative=story.get("narrative", ""),
        symbol=symbol,
        total_latency_ms=proof.get("total_latency_ms"),
    )
    steps.append(
        {
            "step": len(steps) + 1,
            "agent_id": PROOF_MEDIA_ID,
            "worker": PROOF_MEDIA_NAME,
            "capability": "proof_broadcast",
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
            "output": share,
        }
    )

    stats = hub_stats or {}
    t0 = time.perf_counter()
    capital = await scan_fundraise_signals_async(
        total_revenue_usd=float(stats.get("total_revenue_usd", 0)),
        mesh_proofs=int(stats.get("mesh_proofs", 0)),
        total_agents=int(stats.get("total_agents", len(ECOSYSTEM_ASSEMBLY_AGENTS))),
        tvl_usd=float(stats.get("tvl_usd", 0)),
    )
    steps.append(
        {
            "step": len(steps) + 1,
            "agent_id": CAPITAL_ID,
            "worker": CAPITAL_NAME,
            "capability": "fund_radar",
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
            "output": capital,
        }
    )
    dialogue.say(
        CAPITAL_ID,
        ORCHESTRATOR_ID,
        f"Sermaye sinyali: {capital.get('readiness')} — ekosistem birleşti",
        intent="assembly_done",
        thread_id=thread_id,
    )

    total_ms = round((time.perf_counter() - started) * 1000, 1)
    assembly_id = f"asm_{uuid.uuid4().hex[:10]}"

    return {
        "assembly_id": assembly_id,
        "pipeline": "ecosystem_assembly",
        "symbol": symbol,
        "proof_id": proof.get("proof_id"),
        "mesh_verdict": proof.get("verdict"),
        "workers_used": len(steps) + (len(proof_steps) if not skip_mesh_proof else 0),
        "assembly_steps": len(steps),
        "steps": steps,
        "mesh_proof_steps": len(proof_steps),
        "story": story,
        "brand": brand,
        "outreach": outreach,
        "share_card": share,
        "capital_signal": capital,
        "dialogue_thread": thread_id,
        "dialogue_messages": len([m for m in dialogue.list_messages(thread_id=thread_id, limit=200)]),
        "total_latency_ms": total_ms,
        "agents_in_ecosystem": list(ECOSYSTEM_ASSEMBLY_AGENTS),
        "real_data": True,
    }
