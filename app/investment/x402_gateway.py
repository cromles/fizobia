from __future__ import annotations

import base64
import json
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.config import settings

MARKET_PULSE_RESOURCE = "/hub/x402/market-pulse/analyze"
SENTIMENT_RADAR_RESOURCE = "/hub/x402/sentiment-radar/analyze"


@dataclass(frozen=True)
class X402ServiceSpec:
    service_id: str
    agent_id: str
    name: str
    description: str
    resource_path: str
    discover_path: str
    data_source: str
    price_setting: str

    def price_usd(self) -> float:
        return float(getattr(settings, self.price_setting))


X402_SERVICES: Dict[str, X402ServiceSpec] = {
    "market-pulse": X402ServiceSpec(
        service_id="market-pulse",
        agent_id="oam.analyst.market.local",
        name="Market-Pulse",
        description="Gerçek CoinGecko verisi ile kripto piyasa analizi",
        resource_path=MARKET_PULSE_RESOURCE,
        discover_path="/hub/x402/market-pulse",
        data_source="coingecko",
        price_setting="x402_market_pulse_price_usd",
    ),
    "sentiment-radar": X402ServiceSpec(
        service_id="sentiment-radar",
        agent_id="oam.analyst.sentiment.local",
        name="Sentiment-Radar",
        description="Fear & Greed endeksi + haber metni sentiment analizi",
        resource_path=SENTIMENT_RADAR_RESOURCE,
        discover_path="/hub/x402/sentiment-radar",
        data_source="alternative.me+fng+lexicon",
        price_setting="x402_sentiment_radar_price_usd",
    ),
}


def market_pulse_price_usd() -> float:
    return X402_SERVICES["market-pulse"].price_usd()


def sentiment_radar_price_usd() -> float:
    return X402_SERVICES["sentiment-radar"].price_usd()


def mesh_proof_price_usd() -> float:
    return settings.x402_mesh_proof_price_usd


MESH_PROOF_RESOURCE = "/hub/proof/mesh/run"


def service_price_usd(service_id: str) -> float:
    spec = X402_SERVICES.get(service_id)
    if spec is None:
        raise ValueError(f"Bilinmeyen x402 servisi: {service_id}")
    return spec.price_usd()


def usdc_atomic_amount(amount_usd: float) -> str:
    return str(int(round(amount_usd * 1_000_000)))


def build_mesh_proof_payment_required(*, symbol: str = "bitcoin") -> Dict[str, Any]:
    amount = mesh_proof_price_usd()
    base = settings.public_base_url.rstrip("/")
    pay_to = settings.x402_payee_address or "0x0000000000000000000000000000000000000000"
    return {
        "x402Version": 1,
        "error": "payment_required",
        "message": "Mesh Kanıtı — 3 gerçek işçi pipeline için USDC ödemesi gerekli",
        "accepts": [
            {
                "scheme": "exact",
                "network": settings.x402_network,
                "maxAmountRequired": usdc_atomic_amount(amount),
                "resource": f"{base}{MESH_PROOF_RESOURCE}",
                "description": f"Web crawl → Sentiment → Market ({symbol}) — mock yok",
                "mimeType": "application/json",
                "payTo": pay_to,
                "maxTimeoutSeconds": 300,
                "asset": "USDC",
                "extra": {
                    "service_id": "mesh-proof",
                    "price_usd": amount,
                    "symbol": symbol,
                    "workers": 3,
                },
            }
        ],
        "service": {
            "service_id": "mesh-proof",
            "name": "OAM Mesh Proof",
            "workers": ["Web-Crawler-Pro", "Sentiment-Radar", "Market-Pulse"],
            "real_data_source": "coindesk+alternative.me+coingecko",
            "revenue_split_staking_pct": 65,
        },
    }


def build_payment_required(
    service_id: str,
    *,
    context_label: str = "",
) -> Dict[str, Any]:
    spec = X402_SERVICES[service_id]
    amount = spec.price_usd()
    base = settings.public_base_url.rstrip("/")
    pay_to = settings.x402_payee_address or "0x0000000000000000000000000000000000000000"
    label = context_label or spec.service_id
    return {
        "x402Version": 1,
        "error": "payment_required",
        "message": f"{spec.name} için USDC ödemesi gerekli",
        "accepts": [
            {
                "scheme": "exact",
                "network": settings.x402_network,
                "maxAmountRequired": usdc_atomic_amount(amount),
                "resource": f"{base}{spec.resource_path}",
                "description": f"{spec.description} — {label}",
                "mimeType": "application/json",
                "payTo": pay_to,
                "maxTimeoutSeconds": 300,
                "asset": "USDC",
                "extra": {
                    "service_id": spec.service_id,
                    "agent_id": spec.agent_id,
                    "price_usd": amount,
                    "name": spec.name,
                    "context": label,
                },
            }
        ],
        "service": {
            "service_id": spec.service_id,
            "agent_id": spec.agent_id,
            "name": spec.name,
            "real_data_source": spec.data_source,
            "revenue_split_staking_pct": 65,
        },
    }


def parse_payment_proof(
    payment_header: Optional[str],
    payment_proof_header: Optional[str],
    *,
    required_usd: float,
) -> Dict[str, Any]:
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

    if amount_f + 1e-9 < required_usd:
        raise ValueError(f"Yetersiz ödeme: {amount_f} < {required_usd} USDC")

    payer = raw.get("payer") or raw.get("from") or raw.get("payerAddress")
    payment_id = raw.get("payment_id") or raw.get("paymentId") or f"x402_{uuid.uuid4().hex[:16]}"
    tx_hash = raw.get("tx_hash") or raw.get("transactionHash")

    if tx_hash and not settings.x402_dev_accept_proof:
        from app.investment.x402_chain_verify import verify_usdc_transfer

        chain = verify_usdc_transfer(str(tx_hash), min_amount_usdc=required_usd)
        return {
            "amount_usdc": chain["amount_usdc"],
            "payer": chain.get("payer") or payer,
            "payment_id": payment_id,
            "network": chain.get("network") or settings.x402_network,
            "asset": "USDC",
            "tx_hash": chain["tx_hash"],
            "verified_on_chain": True,
        }

    if tx_hash and settings.x402_dev_accept_proof:
        try:
            from app.investment.x402_chain_verify import verify_usdc_transfer

            chain = verify_usdc_transfer(str(tx_hash), min_amount_usdc=required_usd)
            return {
                "amount_usdc": chain["amount_usdc"],
                "payer": chain.get("payer") or payer,
                "payment_id": payment_id,
                "network": chain.get("network") or settings.x402_network,
                "asset": "USDC",
                "tx_hash": chain["tx_hash"],
                "verified_on_chain": True,
            }
        except Exception:
            pass

    return {
        "amount_usdc": round(amount_f, 8),
        "payer": payer,
        "payment_id": payment_id,
        "network": raw.get("network") or settings.x402_network,
        "asset": raw.get("asset") or "USDC",
    }


class PaymentRequiredError(Exception):
    pass


def list_x402_services() -> Dict[str, Any]:
    base = settings.public_base_url.rstrip("/")
    services = []
    for spec in X402_SERVICES.values():
        price = spec.price_usd()
        services.append(
            {
                "id": spec.service_id,
                "agent_id": spec.agent_id,
                "name": spec.name,
                "description": spec.description,
                "price_usdc": price,
                "real_data": True,
                "data_source": spec.data_source,
                "methods": {
                    "discover": f"{base}{spec.discover_path}",
                    "analyze": f"{base}{spec.resource_path}",
                    "revenue_webhook": f"{base}/hub/revenue/x402",
                },
            }
        )
    services.append(
        {
            "id": "mesh-proof",
            "agent_id": "oam.mesh.proof",
            "name": "Mesh Kanıtı",
            "description": "3 gerçek işçi zinciri: web crawl → sentiment → market (tek ödeme)",
            "price_usdc": mesh_proof_price_usd(),
            "real_data": True,
            "data_source": "coindesk+alternative.me+coingecko",
            "methods": {
                "discover": f"{base}/hub/proof/mesh",
                "run": f"{base}{MESH_PROOF_RESOURCE}",
                "revenue_webhook": f"{base}/hub/revenue/x402",
            },
        }
    )
    return {
        "protocol": "x402",
        "version": 1,
        "services": services,
    }
