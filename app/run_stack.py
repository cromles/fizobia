from __future__ import annotations

import asyncio
import logging
import multiprocessing
import os
import time

# Gerçek entegrasyon: demo kapalı, canlı görev döngüsü açık
os.environ.setdefault("OAM_HUB_DEMO", "false")
os.environ.setdefault("OAM_HUB_LIVE_INTERVAL", "30")

from app.config import settings
from app.main import run_gateway, run_mock_fetcher, run_mock_synthesizer, run_mock_transformer

logger = logging.getLogger(__name__)


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
    print("Ajanlar başlatılıyor (3s)…")
    time.sleep(3)

    gateway = _run(run_gateway, "oam-gateway")
    processes = agent_processes + [gateway]

    port = settings.gateway_port
    print("OAM canlı yığın başlatıldı (GERÇEK MOD):")
    print(f"  The Hub:     http://127.0.0.1:{port}/hub")
    print(f"  Gateway:     http://127.0.0.1:{port}")
    print(f"  Hub Live:    http://127.0.0.1:{port}/hub/live")
    print("  Fetcher:     http://127.0.0.1:8101")
    print("  Synthesizer: http://127.0.0.1:8102")
    print("  Transformer: http://127.0.0.1:8103")
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
