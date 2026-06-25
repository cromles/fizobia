"""OAM tam yığın demo — gateway + 3 örnek ajan sürecini başlatır."""

from __future__ import annotations

import multiprocessing
import time

from app.config import settings
from app.main import run_gateway, run_mock_fetcher, run_mock_synthesizer, run_mock_transformer


def _run(proc_target, name: str) -> multiprocessing.Process:
    process = multiprocessing.Process(target=proc_target, name=name, daemon=True)
    process.start()
    return process


def main() -> None:
    processes = [
        _run(run_mock_fetcher, "oam-fetcher"),
        _run(run_mock_synthesizer, "oam-synthesizer"),
        _run(run_mock_transformer, "oam-transformer"),
        _run(run_gateway, "oam-gateway"),
    ]
    print("OAM yığını başlatıldı:")
    print(f"  Gateway:     http://127.0.0.1:{settings.gateway_port}")
    print("  Fetcher:     http://127.0.0.1:8101")
    print("  Synthesizer: http://127.0.0.1:8102")
    print("  Transformer: http://127.0.0.1:8103")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nKapatılıyor...")
        for process in processes:
            process.terminate()


if __name__ == "__main__":
    main()
