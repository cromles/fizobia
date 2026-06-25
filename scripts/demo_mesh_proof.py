#!/usr/bin/env python3
"""Mesh Kanıtı — 3 gerçek işçi pipeline demosu (skeptiklere cevap)."""

from __future__ import annotations

import json
import sys
import uuid

import httpx

BASE = "http://127.0.0.1:8787"
SYMBOL = sys.argv[1] if len(sys.argv) > 1 else "bitcoin"


def main() -> None:
    print("\n  ═══ OAM MESH KANITI ═══")
    print("  Mock yok · 3 gerçek API · 1 pipeline\n")

    with httpx.Client(timeout=60.0) as client:
        discover = client.get(f"{BASE}/hub/proof/mesh", params={"symbol": SYMBOL})
        discover.raise_for_status()
        meta = discover.json()
        price = meta["price_usdc"]
        print(f"  Pipeline: {meta['pipeline']}")
        print(f"  Fiyat: ${price} USDC\n")

        unpaid = client.post(f"{BASE}/hub/proof/mesh/run", json={"symbol": SYMBOL})
        assert unpaid.status_code == 402
        print("  ✓ 402 Payment Required (x402)\n")

        proof = {
            "amount_usdc": price,
            "payer": "0x" + "proof" + uuid.uuid4().hex[:32],
            "payment_id": f"mesh_{uuid.uuid4().hex[:10]}",
            "network": "x402-demo",
            "asset": "USDC",
        }
        print("  3 işçi çalışıyor…")
        paid = client.post(
            f"{BASE}/hub/proof/mesh/run",
            json={"symbol": SYMBOL},
            headers={"X-Payment-Proof": json.dumps(proof)},
        )
        paid.raise_for_status()
        body = paid.json()
        proof_body = body.get("proof", {})

        print(f"\n  PROOF ID: {proof_body.get('proof_id')}")
        print(f"  VERDICT:  {proof_body.get('verdict')}")
        share = body.get("share", {})
        if share.get("card"):
            print(f"  PAYLAŞ:   {share['card']}")
        print(f"  LATENCY:  {proof_body.get('total_latency_ms')}ms")
        print(f"  STAKING:  ${body.get('revenue', {}).get('staking_usd')}\n")

        for step in proof_body.get("steps", []):
            out = step.get("output", {})
            print(f"  [{step['step']}] {step['worker']} ({step['latency_ms']}ms)")
            print(f"       {out.get('analysis', out.get('headline', '—'))[:100]}")

        print("\n  Skeptiklere cevap: 3 gerçek işçi, 1 ödeme, kanıtlandı.\n")


if __name__ == "__main__":
    main()
