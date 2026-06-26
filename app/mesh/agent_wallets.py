"""Ajan mikro cüzdanları — görev başına anlık ödeme defteri."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WalletEntry:
    entry_id: str
    agent_id: str
    amount_usdc: float
    reason: str
    job_id: str
    payer: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    def to_public(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "agent_id": self.agent_id,
            "amount_usdc": round(self.amount_usdc, 6),
            "reason": self.reason,
            "job_id": self.job_id,
            "payer": self.payer,
            "timestamp": self.timestamp,
        }


@dataclass
class AgentWallet:
    agent_id: str
    wallet_id: str
    balance_usdc: float = 0.0
    earned_usdc: float = 0.0
    tasks_won: int = 0
    tasks_lost: int = 0
    last_job_id: str = ""

    def to_public(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "wallet_id": self.wallet_id,
            "balance_usdc": round(self.balance_usdc, 6),
            "earned_usdc": round(self.earned_usdc, 6),
            "tasks_won": self.tasks_won,
            "tasks_lost": self.tasks_lost,
            "last_job_id": self.last_job_id,
        }


_wallets: Dict[str, AgentWallet] = {}
_ledger: List[WalletEntry] = []


def wallet_id_for_agent(agent_id: str) -> str:
    """Deterministik iç cüzdan kimliği."""
    digest = uuid.uuid5(uuid.NAMESPACE_URL, f"oam-wallet:{agent_id}").hex
    return "0x" + digest[:40]


def get_wallet(agent_id: str) -> AgentWallet:
    if agent_id not in _wallets:
        _wallets[agent_id] = AgentWallet(
            agent_id=agent_id,
            wallet_id=wallet_id_for_agent(agent_id),
        )
    return _wallets[agent_id]


def credit_agent(
    agent_id: str,
    amount_usdc: float,
    *,
    reason: str,
    job_id: str,
    payer: str | None = None,
) -> WalletEntry:
    if amount_usdc <= 0:
        raise ValueError("Mikro ödeme sıfır olamaz")
    wallet = get_wallet(agent_id)
    wallet.balance_usdc += amount_usdc
    wallet.earned_usdc += amount_usdc
    wallet.tasks_won += 1
    wallet.last_job_id = job_id
    entry = WalletEntry(
        entry_id=f"wlt_{uuid.uuid4().hex[:10]}",
        agent_id=agent_id,
        amount_usdc=amount_usdc,
        reason=reason,
        job_id=job_id,
        payer=payer,
    )
    _ledger.append(entry)
    return entry


def record_loss(agent_id: str, *, job_id: str) -> None:
    wallet = get_wallet(agent_id)
    wallet.tasks_lost += 1
    wallet.last_job_id = job_id


def list_wallets(*, limit: int = 50) -> List[Dict[str, Any]]:
    items = sorted(_wallets.values(), key=lambda w: -w.earned_usdc)
    return [w.to_public() for w in items[:limit]]


def list_ledger(*, job_id: str | None = None, limit: int = 100) -> List[Dict[str, Any]]:
    entries = _ledger
    if job_id:
        entries = [e for e in entries if e.job_id == job_id]
    return [e.to_public() for e in entries[-limit:]]


def reset_wallets() -> None:
    _wallets.clear()
    _ledger.clear()
