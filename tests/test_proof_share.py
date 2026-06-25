from unittest.mock import patch

import pytest

from app.investment.x402_chain_verify import verify_usdc_transfer
from app.mesh.proof_vault import get_proof_vault

_TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
_USDC = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
_PAYEE = "0x00000000000000000000000000000000000000aa"
_PAYER = "0x00000000000000000000000000000000000000bb"


def _mock_receipt():
    amount = 100_000  # 0.1 USDC
    return {
        "status": "0x1",
        "logs": [
            {
                "address": _USDC,
                "topics": [
                    _TRANSFER,
                    "0x" + "0" * 24 + _PAYER[2:],
                    "0x" + "0" * 24 + _PAYEE[2:],
                ],
                "data": hex(amount),
            }
        ],
    }


@patch("app.investment.x402_chain_verify._rpc_call")
def test_verify_usdc_transfer_ok(mock_rpc):
    mock_rpc.return_value = _mock_receipt()
    result = verify_usdc_transfer(
        "0x" + "a" * 64,
        min_amount_usdc=0.05,
        payee=_PAYEE,
        rpc_url="http://rpc.test",
        usdc_contract=_USDC,
    )
    assert result["verified_on_chain"] is True
    assert result["amount_usdc"] == 0.1
    assert result["payer"].lower() == _PAYER.lower()


def test_proof_vault_store_and_list():
    vault = get_proof_vault()
    before = vault.stats()["proofs_recorded"]
    vault.store(
        {
            "proof_id": "proof_unit_test",
            "verdict": "test",
            "pipeline": "a→b→c",
            "symbol": "btc",
            "total_latency_ms": 100,
            "steps": [{"worker": "W", "latency_ms": 1, "output": {"analysis": "x"}}],
        },
        paid_usdc=0.1,
        staking_usdc=0.065,
        payer="0x" + "1" * 40,
    )
    assert vault.get("proof_unit_test") is not None
    assert vault.stats()["proofs_recorded"] >= before + 1
