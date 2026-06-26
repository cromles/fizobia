#!/usr/bin/env python3
"""Kurucu ajan ekosistemi demosu — işe alma + büyüme olayları."""

from __future__ import annotations

import json
import sys
import urllib.request

from app.config import settings

BASE = settings.public_base_url.rstrip("/")


def get(path: str) -> dict:
    with urllib.request.urlopen(f"{BASE}{path}", timeout=30) as resp:
        return json.loads(resp.read().decode())


def post(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    print("\n=== Axium Ekosistem Demo ===\n")

    eco = get("/hub/ecosystem")
    print(f"Felsefe: {eco.get('philosophy')}")
    print(f"Kurucular: {eco.get('founder_count')} | Büyüme: {eco.get('growth_count')}")
    for f in eco.get("founders", []):
        print(f"  · [{f.get('role')}] {f.get('display_name')} — {f.get('mission', '')[:50]}")

    print("\n--- Koordinatör işe alıyor (mesh proof) ---")
    hire = post("/hub/ecosystem/hire", {"pipeline": "mesh_proof", "symbol": "bitcoin"})
    print(f"İşe alınan: {hire.get('hired_agents')}")
    print(f"Kanıt: {hire.get('proof_id')}")
    print(f"Verdict: {hire.get('verdict', '')[:100]}")

    print("\n--- Son olaylar ---")
    events = get("/hub/ecosystem/events?limit=5")
    for ev in events.get("events", []):
        print(f"  [{ev.get('event_type')}] {ev.get('message')}")

    print("\nHub: {}/hub\n".format(BASE))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        print("Önce: bash scripts/start_founder_stack.sh", file=sys.stderr)
        raise SystemExit(1) from exc
