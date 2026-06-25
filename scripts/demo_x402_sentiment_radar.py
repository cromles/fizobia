#!/usr/bin/env python3
"""x402 demo — Sentiment-Radar (Fear & Greed + metin sentiment)."""

from __future__ import annotations

import json
import sys
import uuid

import httpx

BASE = "http://127.0.0.1:8787"
TEXT = (
    sys.argv[1]
    if len(sys.argv) > 1
    else "Bitcoin ETF inflows rise while macro risk stays elevated"
)


def main() -> None:
    print(f"\n  Sentiment-Radar x402 demo\n  text={TEXT[:60]}…\n")

    with httpx.Client(timeout=30.0) as client:
        discover = client.get(f"{BASE}/hub/x402/sentiment-radar", params={"text": TEXT})
        discover.raise_for_status()
        price = discover.json().get("price_usdc", 0.04)
        print(f"   Fiyat: ${price} USDC\n")

        unpaid = client.post(f"{BASE}/hub/x402/sentiment-radar/analyze", json={"text": TEXT})
        assert unpaid.status_code == 402, unpaid.text
        print("   ✓ 402 Payment Required\n")

        proof = {
            "amount_usdc": price,
            "payer": "0x" + "demo" + uuid.uuid4().hex[:32],
            "payment_id": f"demo_{uuid.uuid4().hex[:12]}",
            "network": "x402-demo",
            "asset": "USDC",
        }
        paid = client.post(
            f"{BASE}/hub/x402/sentiment-radar/analyze",
            json={"text": TEXT},
            headers={"X-Payment-Proof": json.dumps(proof)},
        )
        paid.raise_for_status()
        body = paid.json()
        analysis = body.get("analysis", {})
        print(f"   ✓ {analysis.get('analysis', analysis)}")
        print(f"   ✓ sentiment={analysis.get('sentiment')} fg={analysis.get('fear_greed_index')}")
        print(f"   ✓ Gelir staking: ${body.get('revenue', {}).get('staking_usd')}\n")


if __name__ == "__main__":
    main()
