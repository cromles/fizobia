#!/usr/bin/env python3
"""İlk x402 ödeme demosu — Market-Pulse gerçek CoinGecko analizi."""

from __future__ import annotations

import json
import sys
import uuid

import httpx

BASE = "http://127.0.0.1:8787"
SYMBOL = sys.argv[1] if len(sys.argv) > 1 else "bitcoin"


def main() -> None:
    print(f"\n  Market-Pulse x402 demo — symbol={SYMBOL}\n")

    with httpx.Client(timeout=30.0) as client:
        print("1) Keşif (ödeme gereksinimleri)…")
        discover = client.get(f"{BASE}/hub/x402/market-pulse", params={"symbol": SYMBOL})
        discover.raise_for_status()
        price = discover.json().get("price_usdc", 0.05)
        print(f"   Fiyat: ${price} USDC · kaynak: CoinGecko\n")

        print("2) Ödeme olmadan analyze → 402 bekleniyor…")
        unpaid = client.post(
            f"{BASE}/hub/x402/market-pulse/analyze",
            json={"symbol": SYMBOL},
        )
        print(f"   HTTP {unpaid.status_code}")
        if unpaid.status_code == 402:
            print("   ✓ Payment Required (x402)\n")
        else:
            print(unpaid.text)
            sys.exit(1)

        proof = {
            "amount_usdc": price,
            "payer": "0x" + "demo" + uuid.uuid4().hex[:32],
            "payment_id": f"demo_{uuid.uuid4().hex[:12]}",
            "network": "x402-demo",
            "asset": "USDC",
        }
        print("3) Ödeme kanıtı ile analyze…")
        paid = client.post(
            f"{BASE}/hub/x402/market-pulse/analyze",
            json={"symbol": SYMBOL},
            headers={"X-Payment-Proof": json.dumps(proof)},
        )
        print(f"   HTTP {paid.status_code}")
        paid.raise_for_status()
        body = paid.json()
        analysis = body.get("analysis", {})
        revenue = body.get("revenue", {})
        print(f"   ✓ {analysis.get('analysis', analysis)}")
        print(f"   ✓ Gelir: ${revenue.get('gross_usd')} (staking ${revenue.get('staking_usd')})")
        print(f"   ✓ Kaynak: {analysis.get('source')} · real_data={analysis.get('real_data')}\n")
        print("İlk x402 ödeme tamamlandı. /hub/live feed'de görünecek.\n")


if __name__ == "__main__":
    main()
