#!/usr/bin/env python3
"""Axium production — canlı sunucu gerçek testleri."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

BASE = "https://axium.com.tr"
TIMEOUT = 90.0


@dataclass
class Result:
    name: str
    ok: bool
    detail: str = ""
    ms: float = 0.0


@dataclass
class Suite:
    results: List[Result] = field(default_factory=list)

    def record(self, name: str, ok: bool, detail: str = "", ms: float = 0.0) -> None:
        self.results.append(Result(name, ok, detail, ms))
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {name}" + (f" — {detail}" if detail else "") + (f" ({ms:.0f}ms)" if ms else ""))

    def failed(self) -> List[Result]:
        return [r for r in self.results if not r.ok]


def req(
    method: str,
    path: str,
    *,
    payload: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = TIMEOUT,
) -> tuple[int, Any, float]:
    url = f"{BASE.rstrip('/')}{path}"
    hdrs = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            body = resp.read().decode()
            ms = (time.perf_counter() - t0) * 1000
            try:
                return resp.status, json.loads(body), ms
            except json.JSONDecodeError:
                return resp.status, body[:500], ms
    except urllib.error.HTTPError as exc:
        ms = (time.perf_counter() - t0) * 1000
        raw = exc.read().decode(errors="replace")
        try:
            return exc.code, json.loads(raw), ms
        except json.JSONDecodeError:
            return exc.code, raw[:500], ms


def payment_proof(payment_id: str) -> str:
    return json.dumps(
        {
            "amount_usdc": 0.10,
            "payer": "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "payment_id": payment_id,
        }
    )


def run_suite() -> Suite:
    s = Suite()
    print(f"\n  Axium Production Test — {BASE}\n")

    code, body, ms = req("GET", "/hub/version")
    build = body.get("hub_build", "?") if isinstance(body, dict) else "?"
    s.record("hub/version", code == 200 and "free-apis" in str(build), f"build={build}", ms)

    code, body, ms = req("GET", "/hub/llm")
    if isinstance(body, dict):
        llm_ok = body.get("enabled") is True and body.get("provider") == "gemini"
        s.record("hub/llm gemini", llm_ok, f"{body.get('provider')} · {body.get('default_model')}", ms)
    else:
        s.record("hub/llm gemini", False, str(body)[:80], ms)

    code, body, ms = req("GET", "/hub/apis")
    if isinstance(body, dict):
        s.record("hub/apis", code == 200 and body.get("free_no_auth", 0) >= 6, f"free={body.get('free_no_auth')}", ms)
    else:
        s.record("hub/apis", False, str(body)[:80], ms)

    for path, key in (
        ("/hub/data/fx?symbols=TRY", "usd_try"),
        ("/hub/data/defi?limit=5", "leader_chain"),
        ("/hub/data/btc-network", "btc_usd"),
    ):
        code, body, ms = req("GET", path, timeout=30)
        ok = code == 200 and isinstance(body, dict) and body.get("real_data") is True and key in body
        val = body.get(key) if isinstance(body, dict) else "?"
        s.record(f"GET {path.split('?')[0]}", ok, f"{key}={val}", ms)

    code, body, ms = req("GET", "/hub/departments")
    if isinstance(body, dict):
        s.record("hub/departments", code == 200 and body.get("count") == 3, f"{body.get('count')} dept", ms)
    else:
        s.record("hub/departments", False, str(body)[:80], ms)

    code, body, ms = req("GET", "/hub/ecosystem")
    if isinstance(body, dict):
        agents = body.get("total_agents", 0)
        s.record("hub/ecosystem", code == 200 and agents >= 15, f"{agents} agents", ms)
    else:
        s.record("hub/ecosystem", False, str(body)[:80], ms)

  # ── Şiir (quick_compose + Gemini) ──
    poem_prompt = "bana şiir yaz aşk şiiri olsun"
    code, body, ms = req(
        "POST",
        "/hub/prompt",
        payload={"prompt": poem_prompt, "background_music": True, "duration_sec": 30},
        headers={"X-Payment-Proof": payment_proof("live_poem_test")},
        timeout=120,
    )
    if code == 200 and isinstance(body, dict):
        result = body.get("result") or body
        mode = result.get("mode", "")
        winner = result.get("winner") or {}
        render = result.get("render") or {}
        script = render.get("text") or winner.get("script") or ""
        words = len(script.split())
        lines = len([ln for ln in script.splitlines() if ln.strip()])
        ok = mode == "quick_compose" and words >= 40 and lines >= 6
        src = render.get("source") or result.get("real_data")
        llm_hint = "llm" if str(src).startswith("llm") or result.get("real_data") else str(src)
        s.record(
            "POST /hub/prompt şiir",
            ok,
            f"mode={mode} · {words}w · {lines}ln · {llm_hint} · {ms/1000:.1f}s",
            ms,
        )
        if script and len(script) < 400:
            print(f"       önizleme: {script[:200]}…")
    else:
        s.record("POST /hub/prompt şiir", False, f"HTTP {code} {str(body)[:100]}", ms)

    # ── Reels arena ──
    reels_prompt = "30 saniyelik instagram reels teknoloji haberleri dikey video"
    code, body, ms = req(
        "POST",
        "/hub/prompt",
        payload={"prompt": reels_prompt, "background_music": True, "duration_sec": 30},
        headers={"X-Payment-Proof": payment_proof("live_arena_test")},
        timeout=120,
    )
    if code == 200 and isinstance(body, dict):
        result = body.get("result") or body
        mode = result.get("mode", "arena")
        winner = result.get("winner") or {}
        script = winner.get("script") or ""
        words = len(script.split())
        score = winner.get("critic_score", 0)
        ok = mode != "quick_compose" and words >= 25 and score >= 0.2
        s.record(
            "POST /hub/prompt reels",
            ok,
            f"mode={mode} · {words} kelime · skor={score:.0%}",
            ms,
        )
    else:
        s.record("POST /hub/prompt reels", False, f"HTTP {code} {str(body)[:100]}", ms)

    # ── x402 market pulse ──
    code, body, ms = req(
        "POST",
        "/hub/x402/market-pulse/analyze",
        payload={"symbol": "bitcoin"},
        headers={"X-Payment-Proof": payment_proof("live_market_test")},
        timeout=30,
    )
    if code == 200 and isinstance(body, dict):
        analysis = body.get("analysis") or {}
        price = analysis.get("price_usd")
        s.record("x402 market-pulse", analysis.get("real_data") is True and price, f"BTC ${price}", ms)
    else:
        s.record("x402 market-pulse", False, f"HTTP {code}", ms)

    # ── mesh proof ──
    code, body, ms = req(
        "POST",
        "/hub/proof/mesh/run",
        payload={"symbol": "bitcoin"},
        headers={"X-Payment-Proof": payment_proof("live_mesh_test")},
        timeout=60,
    )
    if code == 200 and isinstance(body, dict):
        proof = body.get("proof") or body.get("result") or body
        steps = proof.get("steps") or []
        s.record("mesh proof pipeline", len(steps) >= 3, f"{len(steps)} adım · {proof.get('verdict','')[:50]}", ms)

    return s


def main() -> int:
    suite = run_suite()
    failed = suite.failed()
    passed = len(suite.results) - len(failed)
    print(f"\n  Sonuç: {passed}/{len(suite.results)} geçti")
    if failed:
        print("  Başarısız:")
        for r in failed:
            print(f"    - {r.name}: {r.detail}")
        return 1
    print("  ✓ Tüm canlı testler geçti\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
