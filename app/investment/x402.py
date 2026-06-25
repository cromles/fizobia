from __future__ import annotations

import hashlib
import hmac
import re
from typing import Any, Dict, Optional

from app.config import settings

_TX_RE = re.compile(r"^0x[a-fA-F0-9]{64}$")
_ADDR_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")


def verify_webhook_secret(provided: Optional[str]) -> bool:
    """x402 webhook imzası — secret yapılandırılmadıysa dev modunda geçer."""
    secret = settings.x402_webhook_secret
    if not secret:
        return True
    if not provided:
        return False
    expected = hmac.new(secret.encode(), b"x402-hub", hashlib.sha256).hexdigest()
    return hmac.compare_digest(provided, expected)


def parse_x402_payment(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    x402 / harici ödeme kanıtını doğrular.
    Beklenen alanlar: agent_id, amount_usdc, payer (opsiyonel), tx_hash (opsiyonel), task_id (opsiyonel)
    """
    agent_id = str(payload.get("agent_id", "")).strip()
    if not agent_id:
        raise ValueError("agent_id gerekli")

    try:
        amount = float(payload.get("amount_usdc", 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("amount_usdc geçersiz") from exc
    if amount <= 0:
        raise ValueError("amount_usdc sıfırdan büyük olmalı")

    payer = payload.get("payer")
    if payer is not None:
        payer = str(payer).strip()
        if payer and not _ADDR_RE.match(payer):
            raise ValueError("payer geçersiz cüzdan adresi")

    tx_hash = payload.get("tx_hash")
    if tx_hash is not None:
        tx_hash = str(tx_hash).strip()
        if tx_hash and not _TX_RE.match(tx_hash):
            raise ValueError("tx_hash geçersiz")

    task_id = str(payload.get("task_id") or f"x402_{agent_id}_{tx_hash or 'direct'}")
    network = str(payload.get("network") or "x402")
    asset = str(payload.get("asset") or "USDC").upper()

    return {
        "agent_id": agent_id,
        "amount_usdc": round(amount, 8),
        "payer": payer,
        "tx_hash": tx_hash,
        "task_id": task_id,
        "network": network,
        "asset": asset,
        "payment_protocol": str(payload.get("payment_protocol") or "x402"),
    }
