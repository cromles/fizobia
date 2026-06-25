#!/usr/bin/env python3
"""Hub canlı entegrasyon doğrulama — gerçek mesh görevi + live feed."""

from __future__ import annotations

import os
import sys

os.environ.setdefault("OAM_HUB_DEMO", "false")

from fastapi.testclient import TestClient

from app.agents.builtins import FETCHER_MANIFEST, SYNTHESIZER_MANIFEST, TRANSFORMER_MANIFEST
from app.api.main import app, router_mesh
from app.investment import factory
from app.registry.agent_registry import InMemoryAgentRegistry


def main() -> int:
    router_mesh.registry = InMemoryAgentRegistry()
    factory._hub = None

    for manifest in (FETCHER_MANIFEST, SYNTHESIZER_MANIFEST, TRANSFORMER_MANIFEST):
        router_mesh.upsert_agent(manifest)

    client = TestClient(app)
    version = client.get("/hub/version").json()
    if version.get("demo_mode") is not False:
        print("FAIL: demo_mode should be false:", version)
        return 1

    trigger = client.post("/hub/trigger-run")
    if trigger.status_code != 200:
        print("FAIL trigger-run:", trigger.status_code, trigger.text)
        return 1

    live = client.get("/hub/live").json()
    real_count = live["network"].get("real_event_count", 0)
    if real_count < 1:
        print("FAIL: no real events in feed", live)
        return 1

    sim_count = sum(1 for e in live["activity_feed"] if e.get("simulated"))
    print(f"OK integration: {real_count} real events, {sim_count} simulated")
    print(f"   agents reachable: {live['network'].get('reachable_agents')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
