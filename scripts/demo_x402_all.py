#!/usr/bin/env python3
"""Her iki canlı x402 işçisini sırayla dener."""

from __future__ import annotations

import subprocess
import sys


def main() -> None:
    scripts = [
        "scripts/demo_x402_market_pulse.py",
        "scripts/demo_x402_sentiment_radar.py",
    ]
    for script in scripts:
        print(f"\n{'='*50}\n  {script}\n{'='*50}")
        rc = subprocess.call([sys.executable, script])
        if rc != 0:
            sys.exit(rc)
    print("\n  Tüm canlı x402 demoları tamam.\n")


if __name__ == "__main__":
    main()
