from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Deque, Dict, List, Optional


@dataclass
class StoredProof:
    proof_id: str
    verdict: str
    pipeline: str
    symbol: str
    total_latency_ms: float
    paid_usdc: float
    staking_usdc: float
    payer: Optional[str]
    steps_summary: List[str]
    created_at: float = field(default_factory=time.time)
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_public(self) -> Dict[str, Any]:
        return {
            "proof_id": self.proof_id,
            "verdict": self.verdict,
            "pipeline": self.pipeline,
            "symbol": self.symbol,
            "total_latency_ms": self.total_latency_ms,
            "paid_usdc": self.paid_usdc,
            "staking_usdc": self.staking_usdc,
            "payer_short": _short_addr(self.payer),
            "steps_summary": self.steps_summary,
            "created_at": self.created_at,
            "share_url_path": f"/hub/proof/share/{self.proof_id}",
            "real_data": True,
        }


def _short_addr(addr: Optional[str]) -> str:
    if not addr or len(addr) < 12:
        return "—"
    return addr[:6] + "…" + addr[-4:]


class ProofVault:
    """Paylaşılabilir mesh kanıtları — skeptiklere link gönder."""

    def __init__(self, max_size: int = 200) -> None:
        self._items: Dict[str, StoredProof] = {}
        self._order: Deque[str] = deque(maxlen=max_size)
        self._lock = Lock()

    def store(
        self,
        proof: Dict[str, Any],
        *,
        paid_usdc: float,
        staking_usdc: float,
        payer: Optional[str] = None,
    ) -> StoredProof:
        proof_id = str(proof.get("proof_id", ""))
        if not proof_id:
            raise ValueError("proof_id gerekli")

        steps_summary = []
        for step in proof.get("steps", []):
            worker = step.get("worker", "?")
            ms = step.get("latency_ms", 0)
            out = step.get("output", {})
            headline = out.get("analysis") or out.get("headline") or "—"
            steps_summary.append(f"{worker} ({ms}ms): {str(headline)[:80]}")

        record = StoredProof(
            proof_id=proof_id,
            verdict=str(proof.get("verdict", "")),
            pipeline=str(proof.get("pipeline", "")),
            symbol=str(proof.get("symbol", "")),
            total_latency_ms=float(proof.get("total_latency_ms", 0)),
            paid_usdc=paid_usdc,
            staking_usdc=staking_usdc,
            payer=payer,
            steps_summary=steps_summary,
            raw=proof,
        )
        with self._lock:
            if proof_id not in self._items:
                self._order.append(proof_id)
            self._items[proof_id] = record
            while len(self._items) > self._order.maxlen:
                old = self._order.popleft()
                self._items.pop(old, None)
        return record

    def get(self, proof_id: str) -> Optional[StoredProof]:
        with self._lock:
            return self._items.get(proof_id)

    def list_recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            ids = list(reversed(self._order))[:limit]
            return [self._items[i].to_public() for i in ids if i in self._items]

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._items)
            paid = sum(p.paid_usdc for p in self._items.values())
            staking = sum(p.staking_usdc for p in self._items.values())
        return {
            "proofs_recorded": total,
            "total_paid_usdc": round(paid, 4),
            "total_staking_usdc": round(staking, 4),
        }


_vault = ProofVault()


def get_proof_vault() -> ProofVault:
    return _vault
