from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx
from eth_utils import keccak, to_checksum_address

from app.config import settings

logger = logging.getLogger(__name__)

_TRANSFER_TOPIC = "0x" + keccak(text="Transfer(address,address,uint256)").hex()
_TX_HASH_OK = 66


def _rpc_call(rpc_url: str, method: str, params: list) -> Any:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    with httpx.Client(timeout=20.0) as client:
        response = client.post(rpc_url, json=payload)
        response.raise_for_status()
        body = response.json()
    if body.get("error"):
        raise ValueError(body["error"].get("message", "RPC hatası"))
    return body.get("result")


def verify_usdc_transfer(
    tx_hash: str,
    *,
    min_amount_usdc: float,
    payee: Optional[str] = None,
    rpc_url: Optional[str] = None,
    usdc_contract: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Sepolia / EVM üzerinde gerçek USDC transfer tx doğrular.
  ERC20 Transfer log: from, to, value
    """
    if not tx_hash or len(tx_hash) != _TX_HASH_OK or not tx_hash.startswith("0x"):
        raise ValueError("Geçersiz tx_hash")

    rpc = rpc_url or settings.x402_rpc_url or settings.onchain_rpc_url
    token = to_checksum_address(usdc_contract or settings.x402_usdc_contract)
    recipient = to_checksum_address(payee or settings.x402_payee_address)
    if not recipient or recipient == "0x0000000000000000000000000000000000000000":
        raise ValueError("x402 payee adresi yapılandırılmamış (OAM_X402_PAYEE_ADDRESS)")

    receipt = _rpc_call(rpc, "eth_getTransactionReceipt", [tx_hash])
    if not receipt or receipt.get("status") != "0x1":
        raise ValueError("İşlem başarısız veya bulunamadı")

    min_atomic = int(round(min_amount_usdc * 1_000_000))
    payer: Optional[str] = None
    amount_atomic = 0

    for log in receipt.get("logs", []):
        if to_checksum_address(log.get("address", "0x" + "0" * 40)) != token:
            continue
        topics = log.get("topics") or []
        if len(topics) < 3 or topics[0].lower() != _TRANSFER_TOPIC.lower():
            continue
        from_addr = "0x" + topics[1][-40:]
        to_addr = "0x" + topics[2][-40:]
        if to_checksum_address(to_addr) != recipient:
            continue
        data = log.get("data", "0x0")
        amount_atomic = int(data, 16)
        payer = to_checksum_address(from_addr)
        break

    if amount_atomic < min_atomic:
        raise ValueError(
            f"Yetersiz USDC transferi: {amount_atomic / 1_000_000:.6f} < {min_amount_usdc}"
        )

    return {
        "tx_hash": tx_hash,
        "payer": payer,
        "payee": recipient,
        "amount_usdc": round(amount_atomic / 1_000_000, 8),
        "network": settings.x402_network,
        "asset": "USDC",
        "verified_on_chain": True,
    }
