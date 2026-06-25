from __future__ import annotations

import multiprocessing
import os
import time

# Gerçek entegrasyon: demo kapalı, canlı görev döngüsü açık
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


def _run(proc_target, name: str) -> multiprocessing.Process:
    process = multiprocessing.Process(target=proc_target, name=name, daemon=True)
    process.start()
    return process


def main() -> None:
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

    print("Ajanlar başlatılıyor (4s)…")
    time.sleep(4)

    gateway = _run(run_gateway, "oam-gateway")
    processes = agent_processes + [gateway]

    port = settings.gateway_port
    total = 3 + len(EXTENDED_MANIFESTS)
    print("OAM canlı yığın başlatıldı (GERÇEK MOD):")
    print(f"  The Hub:     http://127.0.0.1:{port}/hub")
    print(f"  Discovery:   http://127.0.0.1:{port}/hub/discovery")
    print(f"  x402:        http://127.0.0.1:{port}/hub/revenue/x402")
    print(f"  Gateway:     http://127.0.0.1:{port}")
    print(f"  Hub Live:    http://127.0.0.1:{port}/hub/live")
    print(f"  İşçi sayısı: {total} dijital işçi")
    print(f"  Otomatik görev: her {settings.hub_live_interval}s")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nKapatılıyor...")
        for process in processes:
            process.terminate()


if __name__ == "__main__":
    main()
