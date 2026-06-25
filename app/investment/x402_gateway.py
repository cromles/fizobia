from __future__ import annotations

import base64
import json
import uuid
from typing import Any, Dict, Optional

from app.config import settings
from app.workers.market_pulse import AGENT_ID, DISPLAY_NAME

MARKET_PULSE_RESOURCE = "/hub/x402/market-pulse/analyze"


def market_pulse_price_usd() -> float:
    return settings.x402_market_pulse_price_usd


def usdc_atomic_amount(amount_usd: float) -> str:
    """USDC 6 decimal — x402 maxAmountRequired string."""
    return str(int(round(amount_usd * 1_000_000)))


def build_payment_required(symbol: str = "bitcoin") -> Dict[str, Any]:
    """HTTP 402 gövdesi — x402 uyumlu ödeme talebi."""
    amount = market_pulse_price_usd()
    base = settings.public_base_url.rstrip("/")
    pay_to = settings.x402_payee_address or "0x0000000000000000000000000000000000000000"
    return {
        "x402Version": 1,
        "error": "payment_required",
        "message": f"{DISPLAY_NAME} analizi için USDC ödemesi gerekli",
        "accepts": [
            {
                "scheme": "exact",
                "network": settings.x402_network,
                "maxAmountRequired": usdc_atomic_amount(amount),
                "resource": f"{base}{MARKET_PULSE_RESOURCE}",
                "description": f"Gerçek CoinGecko piyasa analizi — {symbol}",
                "mimeType": "application/json",
                "payTo": pay_to,
                "maxTimeoutSeconds": 300,
                "asset": "USDC",
                "extra": {
                    "agent_id": AGENT_ID,
                    "symbol": symbol,
                    "price_usd": amount,
                    "name": DISPLAY_NAME,
                },
            }
        ],
        "service": {
            "agent_id": AGENT_ID,
            "name": DISPLAY_NAME,
            "real_data_source": "coingecko",
            "revenue_split_staking_pct": 65,
        },
    }


def parse_payment_proof(
    payment_header: Optional[str],
    payment_proof_header: Optional[str],
) -> Dict[str, Any]:
    """
  Ödeme kanıtı:
  - X-PAYMENT: base64(JSON) — x402 tarzı
  - X-Payment-Proof: JSON — geliştirme / demo facilitator
    """
    raw: Dict[str, Any] | None = None

    if payment_header:
        try:
            decoded = base64.b64decode(payment_header).decode("utf-8")
            raw = json.loads(decoded)
        except Exception:
            try:
                raw = json.loads(payment_header)
            except Exception:
                raise ValueError("X-PAYMENT geçersiz") from None

    if raw is None and payment_proof_header:
        try:
            raw = json.loads(payment_proof_header)
        except json.JSONDecodeError as exc:
            raise ValueError("X-Payment-Proof geçersiz JSON") from exc

    if raw is None:
        raise PaymentRequiredError()

    amount = raw.get("amount_usdc") or raw.get("amount")
    if amount is None and raw.get("maxAmountRequired"):
        amount = int(raw["maxAmountRequired"]) / 1_000_000
    try:
        amount_f = float(amount)
    except (TypeError, ValueError) as exc:
        raise ValueError("Ödeme tutarı geçersiz") from exc

    required = market_pulse_price_usd()
    if amount_f + 1e-9 < required:
        raise ValueError(f"Yetersiz ödeme: {amount_f} < {required} USDC")

    payer = raw.get("payer") or raw.get("from") or raw.get("payerAddress")
    payment_id = raw.get("payment_id") or raw.get("paymentId") or f"x402_{uuid.uuid4().hex[:16]}"

    return {
        "amount_usdc": round(amount_f, 8),
        "payer": payer,
        "payment_id": payment_id,
        "network": raw.get("network") or settings.x402_network,
        "asset": raw.get("asset") or "USDC",
    }


class PaymentRequiredError(Exception):
    """Ödeme yapılmadan hizmet verilmez."""

    pass


def list_x402_services() -> Dict[str, Any]:
    base = settings.public_base_url.rstrip("/")
    price = market_pulse_price_usd()
    return {
        "protocol": "x402",
        "version": 1,
        "services": [
            {
                "id": "market-pulse",
                "agent_id": AGENT_ID,
                "name": DISPLAY_NAME,
                "description": "Gerçek CoinGecko verisi ile kripto piyasa analizi",
                "price_usdc": price,
                "real_data": True,
                "data_source": "coingecko",
                "methods": {
                    "discover": f"{base}/hub/x402/market-pulse",
                    "analyze": f"{base}{MARKET_PULSE_RESOURCE}",
                    "revenue_webhook": f"{base}/hub/revenue/x402",
                },
            }
        ],
    }
