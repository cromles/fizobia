#!/usr/bin/env python3
"""Canlı OAM yığını entegrasyon doğrulaması."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

from app.config import settings

GATEWAY = f"http://127.0.0.1:{settings.gateway_port}"
AGENTS = {
    "fetcher": ("http://127.0.0.1:8101", "data_fetcher", {"query": "live-test"}),
    "synthesizer": ("http://127.0.0.1:8102", "synthesizer", {"text": "hello mesh"}),
    "transformer": ("http://127.0.0.1:8103", "transform", {"raw_text": "  HELLO  "}),
    "echo": ("http://127.0.0.1:8200", "echo", {"message": "ping"}),
}


def request_json(method: str, url: str, payload: dict | None = None) -> dict:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode())


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "PASS" if condition else "FAIL"
    line = f"[{status}] {name}"
    if detail:
        line += f" — {detail}"
    print(line)
    if not condition:
        raise AssertionError(name)


def main() -> int:
    print("=== OAM Canlı Yığın Testi ===\n")

    health = request_json("GET", f"{GATEWAY}/health")
    check("gateway health", health.get("status") == "ok", json.dumps(health))

    agents = request_json("GET", f"{GATEWAY}/agents")
    check("registry agent sayısı >= 4", len(agents) >= 4, f"{len(agents)} ajan")
    agent_ids = {item["agent_id"] for item in agents}
    check(
        "echo ajanı registry'de",
        "example.echo.agent" in agent_ids,
        ", ".join(sorted(agent_ids)),
    )

    peers = request_json("GET", f"{GATEWAY}/discovery/peers")
    check("DHT peer sayısı >= 4", len(peers) >= 4, f"{len(peers)} peer")

    echo_peers = request_json("GET", f"{GATEWAY}/discovery/peers?capability=echo")
    check("DHT echo capability", len(echo_peers) >= 1)

    for label, (base, capability, data) in AGENTS.items():
        result = request_json(
            "POST",
            f"{base}/execute",
            {"capability": capability, "data": data},
        )
        check(f"doğrudan execute [{label}]", bool(result), json.dumps(result)[:120])

    chain = request_json(
        "POST",
        f"{GATEWAY}/mesh/run",
        {"user_goal": "veri analizi yap", "initial_data": {"query": "integration"}},
    )
    check(
        "mesh zinciri (fetcher→synthesizer)",
        len(chain.get("task_results", {})) >= 2,
        json.dumps(chain.get("proof_of_execution")),
    )
    check(
        "mesh zinciri proof",
        all(chain.get("proof_of_execution", {}).values()),
    )

    echo_run = request_json(
        "POST",
        f"{GATEWAY}/mesh/run",
        {"user_goal": "echo mesajı gönder", "initial_data": {"message": "live-ok"}},
    )
    results = echo_run.get("task_results", {})
    echoed = any(
        isinstance(v, dict) and v.get("message") == "live-ok" for v in results.values()
    )
    check("mesh echo görevi", echoed, json.dumps(results))
    check(
        "mesh echo proof",
        all(echo_run.get("proof_of_execution", {}).values()),
    )

    print("\n=== Tüm canlı testler geçti ===")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, urllib.error.URLError, TimeoutError) as exc:
        print(f"\n[FAIL] {exc}", file=sys.stderr)
        raise SystemExit(1)
