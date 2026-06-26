from __future__ import annotations

import multiprocessing
import os
import time

os.environ.setdefault("OAM_HUB_DEMO", "false")
os.environ.setdefault("OAM_HUB_LIVE_INTERVAL", "30")
os.environ.setdefault("OAM_X402_ENABLED", "true")

from app.agents.extended_builtins import EXTENDED_HANDLERS, EXTENDED_MANIFESTS
from app.config import settings
from app.main import (
    run_extended_agent,
    run_gateway,
    run_mock_fetcher,
    run_mock_synthesizer,
    run_mock_transformer,
)
from app.mesh.founders import FOUNDER_STACK_AGENT_IDS


def _run(proc_target, name: str) -> multiprocessing.Process:
    process = multiprocessing.Process(target=proc_target, name=name, daemon=True)
    process.start()
    return process


def _founder_manifests():
    ids = set(FOUNDER_STACK_AGENT_IDS)
    return [m for m in EXTENDED_MANIFESTS if m.agent_id in ids]


def main() -> None:
    stack_mode = os.getenv("OAM_STACK_MODE", "full").lower()
    agent_processes: list[multiprocessing.Process] = []

    if stack_mode == "founder":
        os.environ["OAM_STACK_MODE"] = "founder"
        for manifest in _founder_manifests():
            port = int(manifest.endpoint.rsplit(":", 1)[-1])
            handlers = EXTENDED_HANDLERS.get(manifest.agent_id, {})
            if not handlers:
                continue
            agent_processes.append(
                _run(
                    lambda m=manifest, p=port, h=handlers: run_extended_agent(m.agent_id, p, h),
                    f"oam-{manifest.agent_id}",
                )
            )
        total = len(agent_processes)
        mode_label = "KURUCU EKOSİSTEM"
    else:
        agent_processes = [
            _run(run_mock_fetcher, "oam-fetcher"),
            _run(run_mock_synthesizer, "oam-synthesizer"),
            _run(run_mock_transformer, "oam-transformer"),
        ]
        for manifest in EXTENDED_MANIFESTS:
            port = int(manifest.endpoint.rsplit(":", 1)[-1])
            handlers = EXTENDED_HANDLERS.get(manifest.agent_id, {})
            if not handlers:
                continue
            agent_processes.append(
                _run(
                    lambda m=manifest, p=port, h=handlers: run_extended_agent(m.agent_id, p, h),
                    f"oam-{manifest.agent_id}",
                )
            )
        total = 3 + len(EXTENDED_MANIFESTS)
        mode_label = "TAM YIĞIN"

    print(f"Ajanlar başlatılıyor ({mode_label}, 4s)…")
    time.sleep(4)

    gateway = _run(run_gateway, "oam-gateway")
    processes = agent_processes + [gateway]

    port = settings.gateway_port
    print(f"OAM yığın başlatıldı — {mode_label}:")
    print(f"  The Hub:       http://127.0.0.1:{port}/hub")
    print(f"  Ekosistem:     http://127.0.0.1:{port}/hub/ecosystem")
    print(f"  İşe alma:      POST /hub/ecosystem/hire")
    print(f"  İşçi sayısı:   {total}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nKapatılıyor...")
        for process in processes:
            process.terminate()


if __name__ == "__main__":
    main()
