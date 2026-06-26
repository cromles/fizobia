from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from app.config import settings

AGENT_ID = "oam.watcher.onchain.local"
DISPLAY_NAME = "On-Chain-Watcher"

_CHAIN_NAMES = {
    84532: "base-sepolia",
    8453: "base",
    11155111: "sepolia",
    1: "ethereum",
}


def fetch_chain_snapshot(*, symbol: str = "bitcoin") -> Dict[str, Any]:
    """Zincir durumu — blok, ağ, x402 hazırlığı (gerçek RPC)."""
    rpc = settings.x402_rpc_url or settings.onchain_rpc_url
    block_hex = _rpc(rpc, "eth_blockNumber", [])
    chain_hex = _rpc(rpc, "eth_chainId", [])
    block_number = int(block_hex, 16)
    chain_id = int(chain_hex, 16)
    network = _CHAIN_NAMES.get(chain_id, settings.x402_network)

    payee = settings.x402_payee_address or ""
    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "real_data": True,
        "symbol": symbol,
        "network": network,
        "chain_id": chain_id,
        "block_number": block_number,
        "rpc_url": rpc.split("//")[-1].split("/")[0] if "//" in rpc else "configured",
        "x402_enabled": settings.x402_enabled,
        "x402_network": settings.x402_network,
        "payee_configured": bool(payee and payee != "0x0000000000000000000000000000000000000000"),
        "analysis": (
            f"Zincir canlı — {network} blok #{block_number:,}. "
            f"x402 {'hazır' if settings.x402_enabled else 'kapalı'}."
        ),
    }


def verify_payment_snapshot(tx_hash: str, *, min_usdc: float = 0.01) -> Dict[str, Any]:
    """USDC transfer doğrulama — x402 ödemeleri için."""
    from app.investment.x402_chain_verify import verify_usdc_transfer

    if settings.x402_dev_accept_proof and tx_hash.startswith("dev_"):
        return {
            "agent_id": AGENT_ID,
            "worker": DISPLAY_NAME,
            "real_data": True,
            "verified_on_chain": False,
            "dev_proof": True,
            "tx_hash": tx_hash,
            "analysis": "Geliştirme proof modu — zincir atlandı",
        }

    verified = verify_usdc_transfer(tx_hash, min_amount_usdc=min_usdc)
    return {
        "agent_id": AGENT_ID,
        "worker": DISPLAY_NAME,
        "real_data": True,
        "verified_on_chain": True,
        **verified,
        "analysis": (
            f"On-chain doğrulandı — {verified.get('amount_usdc')} USDC "
            f"→ {verified.get('payee', '')[:10]}…"
        ),
    }


def _rpc(rpc_url: str, method: str, params: list) -> str:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    with httpx.Client(timeout=15.0) as client:
        response = client.post(rpc_url, json=payload)
        response.raise_for_status()
        body = response.json()
    if body.get("error"):
        raise ValueError(body["error"].get("message", "RPC hatası"))
    result = body.get("result")
    if result is None:
        raise ValueError("RPC boş yanıt")
    return str(result)


async def fetch_chain_snapshot_async(**kwargs: Any) -> Dict[str, Any]:
    import asyncio

    return await asyncio.to_thread(fetch_chain_snapshot, **kwargs)


async def verify_payment_snapshot_async(tx_hash: str, **kwargs: Any) -> Dict[str, Any]:
    import asyncio

    return await asyncio.to_thread(verify_payment_snapshot, tx_hash, **kwargs)
