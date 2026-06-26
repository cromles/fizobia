#!/usr/bin/env python3
"""Departman simülasyonu — üç sektör + makale zinciri birlikte test."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

from app.config import settings

BASE = settings.public_base_url.rstrip("/")
DEMO_PROOF = json.dumps(
    {
        "amount_usdc": 0.10,
        "payer": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "payment_id": "dept_sim_arena",
    }
)


def get(path: str) -> dict:
    with urllib.request.urlopen(f"{BASE}{path}", timeout=60) as resp:
        return json.loads(resp.read().decode())


def post(path: str, payload: dict, *, headers: dict | None = None) -> dict:
    hdrs = {"Content-Type": "application/json", **(headers or {})}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=hdrs, method="POST")
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode())


def section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


def main() -> int:
    print("\n  Axium Departman Simülasyonu")
    print(f"  Hub: {BASE}\n")

    ver = get("/hub/version")
    print(f"Build: {ver.get('hub_build')} | Demo: {ver.get('demo_mode')}")

    section("1 · Departman haritası")
    depts = get("/hub/departments")
    print(depts.get("philosophy", ""))
    for d in depts.get("departments", []):
        print(
            f"  [{d['code']}] {d['label_tr']} — "
            f"{d['registered_count']}/{d['agent_count']} ajan kayıtlı"
        )
    chain = depts.get("article_pipeline", {})
    print(f"\n  Makale zinciri: {' → '.join(s['role'] for s in chain.get('steps', []))}")

    section("2 · Teknik departman — mesh proof")
    t0 = time.perf_counter()
    tech = post("/hub/ecosystem/hire", {"pipeline": "mesh_proof", "symbol": "bitcoin"})
    tech_ms = round((time.perf_counter() - t0) * 1000)
    print(f"  Ajanlar: {', '.join((a.split('.')[-2] if len(a.split('.')) >= 2 else a) for a in tech.get('hired_agents', []))}")
    print(f"  Kanıt: {tech.get('proof_id')} | Verdict: {tech.get('verdict')}")
    print(f"  Diyalog: {tech.get('dialogue_messages')} mesaj | {tech_ms}ms")

    section("3 · Yazılı basın — makale pipeline (4 mikro ajan)")
    t1 = time.perf_counter()
    article = post(
        "/hub/ecosystem/hire",
        {
            "pipeline": "article",
            "goal": "Yapay zeka regülasyonları ve Avrupa AI Act hakkında SEO uyumlu makale",
            "initial_data": {"tone": "corporate"},
        },
    )
    art_ms = round((time.perf_counter() - t1) * 1000)
    print(f"  Departman: {article.get('department')}")
    print(f"  Onay: {'✓' if article.get('approved') else '✗'} | Ton: {article.get('tone')}")
    review = article.get("review") or {}
    print(f"  Immune-Critic skoru: {review.get('critic_score', 0):.0%} — {review.get('verdict', '')}")
    preview = (article.get("final_text") or "")[:220].replace("\n", " ")
    print(f"  Önizleme: {preview}…")
    print(f"  Diyalog: {article.get('dialogue_messages')} mesaj | {art_ms}ms")

    section("4 · Medya departmanı — gladyatör arenası")
    t2 = time.perf_counter()
    arena = post(
        "/hub/prompt",
        {
            "prompt": (
                "Son teknoloji haberleriyle ilgili 30 saniyelik dikey Instagram Reels metni üret."
            ),
            "background_music": True,
            "duration_sec": 30,
        },
        headers={"X-Payment-Proof": DEMO_PROOF},
    )
    arena_ms = round((time.perf_counter() - t2) * 1000)
    winner = arena.get("result", {}).get("winner", {})
    render = arena.get("result", {}).get("render", {})
    print(f"  Kazanan: {winner.get('display_name')} (skor {winner.get('critic_score', 0):.0%})")
    print(f"  Render: {render.get('format')} · {render.get('duration_sec')}s · {render.get('status')}")
    print(f"  Gelir payı: ${arena.get('revenue', {}).get('winner_usdc', 0):.4f} USDC | {arena_ms}ms")

    section("5 · Yatırım liderlik tablosu (departman filtresi)")
    for code in ("technical", "copywriting", "media_video"):
        lb = get(f"/hub/leaderboard?department_code={code}")
        names = [a["display_name"] for a in lb.get("agents", [])[:3]]
        print(f"  [{code}] {lb.get('count', 0)} ajan — önde: {', '.join(names) or '—'}")

    section("6 · Canlı diyalog (makale thread)")
    thread = article.get("dialogue_thread")
    if thread:
        dlg = get(f"/hub/ecosystem/dialogue?thread_id={thread}&limit=8")
        for msg in dlg.get("messages", [])[-6:]:
            aid = msg.get("from_agent", "?")
            parts = aid.split(".")
            who = parts[-2] if len(parts) >= 2 else aid
            text = (msg.get("text") or "")[:90]
            print(f"  {who}: {text}")

    section("Simülasyon tamam")
    total = tech_ms + art_ms + arena_ms
    print(f"  3 departman · 3 pipeline · toplam ~{total}ms")
    print(f"  UI: {BASE}/hub  →  Yatırım sekmesi → departman filtreleri\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()[:300]
        print(f"\nHTTP {exc.code}: {body}", file=sys.stderr)
        print("Önce: bash scripts/start_ecosystem_stack.sh", file=sys.stderr)
        raise SystemExit(1) from exc
    except Exception as exc:
        print(f"\nHATA: {exc}", file=sys.stderr)
        print("Önce: bash scripts/start_ecosystem_stack.sh", file=sys.stderr)
        raise SystemExit(1) from exc
