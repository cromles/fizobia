from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from fastapi import APIRouter, Header, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from app.api.hub_dashboard import render_hub_dashboard
from app.config import settings
from app.core.router import OpenAgentMeshRouter
from app.investment.factory import get_investment_hub
from app.investment.live import build_live_snapshot
from app.investment.discovery_export import (
    build_discovery_catalog,
    build_mpp_descriptor,
    build_platform_agent_card,
)
from app.investment.onchain import (
    build_public_config,
    is_onchain_ready,
    verify_claim_tx,
    verify_stake_tx,
)
from app.investment.schemas import (
    ClaimRewardsRequest,
    PassiveStakeRequest,
    RevenueSplitConfig,
    StakeRequest,
    UnstakeRequest,
    X402RevenueRequest,
)
from app.investment.x402 import parse_x402_payment, verify_webhook_secret
from app.investment.x402_gateway import (
    PaymentRequiredError,
    build_mesh_proof_payment_required,
    build_payment_required,
    list_x402_services,
    market_pulse_price_usd,
    mesh_proof_price_usd,
    parse_payment_proof,
    sentiment_radar_price_usd,
)
from app.mesh.proof_pipeline import MESH_PROOF_AGENTS, run_mesh_proof_pipeline
from app.mesh.growth_protocol import get_growth_protocol
from app.mesh.proof_vault import get_proof_vault
from app.api.hub_ui.proof_card import render_proof_share_card
from app.protocol.schemas import AgentManifest
from app.workers.market_pulse import AGENT_ID as MARKET_PULSE_AGENT_ID, fetch_market_snapshot_async
from app.workers.sentiment_radar import AGENT_ID as SENTIMENT_RADAR_AGENT_ID, fetch_sentiment_snapshot_async
from app.workers.web_crawler import AGENT_ID as WEB_CRAWLER_AGENT_ID


class MarketPulseAnalyzeRequest(BaseModel):
    symbol: str = Field(default="bitcoin", description="btc, eth, sol, bitcoin, ...")


class SentimentRadarAnalyzeRequest(BaseModel):
    text: str = Field(
        default="Bitcoin ETF inflows rise while macro risk stays elevated",
        description="Analiz edilecek haber veya metin",
    )


class MeshProofRunRequest(BaseModel):
    symbol: str = Field(default="bitcoin")
    url: str | None = Field(default=None, description="Opsiyonel RSS/HTML URL")


class EcosystemJoinRequest(BaseModel):
    manifest: AgentManifest


class EcosystemHireRequest(BaseModel):
    pipeline: str = Field(default="mesh_proof", description="mesh_proof | goal")
    goal: str = Field(default="")
    initial_data: Dict[str, Any] = Field(default_factory=dict)
    symbol: str = Field(default="bitcoin")
    url: str | None = None


HUB_BUILD = "2026.06.25-ecosystem-v8"

router = APIRouter(prefix="/hub", tags=["The Hub"])


def _mesh() -> OpenAgentMeshRouter:
    from app.api.main import router_mesh

    return router_mesh


def _embed_frame_header() -> str:
    origins = " ".join(settings.embed_frame_origins)
    return f"frame-ancestors 'self' {origins}"


def _hub_html_response(html: str, *, embed: bool = False) -> HTMLResponse:
    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
        "Surrogate-Control": "no-store",
        "X-Hub-Build": HUB_BUILD,
    }
    if embed:
        headers["Content-Security-Policy"] = _embed_frame_header()
    return HTMLResponse(content=html, headers=headers)


def _render_hub(
    *,
    embed_mode: bool = False,
    brand_title: str = "The Hub",
    brand_sub: str = "Veridag",
) -> HTMLResponse:
    hub = get_investment_hub()
    mesh = _mesh()
    agents = mesh.list_agents()
    cards = hub.list_identity_cards(agents)
    manifests = {m.agent_id: m for m in agents}
    html = render_hub_dashboard(
        cards,
        hub.split,
        manifests,
        build=HUB_BUILD,
        demo_mode=settings.hub_demo_mode,
        onchain=build_public_config(),
        embed_mode=embed_mode,
        brand_title=brand_title,
        brand_sub=brand_sub,
    )
    return _hub_html_response(html, embed=embed_mode)


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def hub_dashboard() -> HTMLResponse:
    return _render_hub()


@router.get("/embed", response_class=HTMLResponse)
async def hub_embed_dashboard() -> HTMLResponse:
    """Zinesh.com iframe embed — protokol markası, landing kapalı."""
    return _render_hub(
        embed_mode=True,
        brand_title="Zinesh Protocol",
        brand_sub="Dijital İşçiler",
    )


@router.get("/sdk/config")
async def hub_sdk_config() -> Dict[str, Any]:
    """Zinesh web sitesi frontend entegrasyonu için public API haritası."""
    base = settings.public_base_url.rstrip("/")
    return {
        "protocol": "OAM-Hub-SDK",
        "version": "1.0",
        "hub_build": HUB_BUILD,
        "api_base": base,
        "embed_url": f"{base}/hub/embed",
        "demo_mode": settings.hub_demo_mode,
        "onchain": build_public_config(),
        "endpoints": {
            "agents": f"{base}/hub/agents",
            "agent": f"{base}/hub/agents/{{agent_id}}",
            "live": f"{base}/hub/live",
            "live_ws": base.replace("https://", "wss://").replace("http://", "ws://") + "/hub/ws/live",
            "stake": f"{base}/hub/stake",
            "claim": f"{base}/hub/claim",
            "positions": f"{base}/hub/positions/{{investor_id}}",
            "revenue_config": f"{base}/hub/revenue/config",
            "onchain_config": f"{base}/hub/onchain/config",
            "version": f"{base}/hub/version",
            "discovery": f"{base}/hub/discovery",
            "partnership_stake": f"{base}/hub/partnership/stake",
            "x402_revenue": f"{base}/hub/revenue/x402",
            "x402_services": f"{base}/hub/x402/services",
            "x402_market_pulse": f"{base}/hub/x402/market-pulse/analyze",
            "x402_sentiment_radar": f"{base}/hub/x402/sentiment-radar/analyze",
            "mesh_proof": f"{base}/hub/proof/mesh/run",
            "ecosystem": f"{base}/hub/ecosystem",
            "ecosystem_join": f"{base}/hub/ecosystem/join",
            "ecosystem_hire": f"{base}/hub/ecosystem/hire",
            "ecosystem_events": f"{base}/hub/ecosystem/events",
            "well_known_agent": f"{base}/.well-known/agent.json",
        },
        "cors_origins": settings.cors_origins,
        "frame_origins": settings.embed_frame_origins,
    }


@router.get("/onchain/config")
async def hub_onchain_config() -> Dict[str, Any]:
    return build_public_config()


@router.get("/version")
async def hub_version() -> Dict[str, Any]:
    return {
        "hub_build": HUB_BUILD,
        "status": "ok",
        "demo_mode": settings.hub_demo_mode,
    }


@router.get("/live")
async def hub_live_feed() -> JSONResponse:
    hub = get_investment_hub()
    agents = _mesh().list_agents()
    return JSONResponse(build_live_snapshot(hub, agents))


@router.websocket("/ws/live")
async def hub_live_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    hub = get_investment_hub()
    try:
        while True:
            agents = _mesh().list_agents()
            snapshot = build_live_snapshot(hub, agents)
            await websocket.send_json(snapshot)
            await asyncio.sleep(max(2.0, settings.hub_live_interval / 4))
    except WebSocketDisconnect:
        return
    except Exception:
        await websocket.close()


@router.post("/trigger-run")
async def hub_trigger_live_run() -> Dict[str, Any]:
    if settings.hub_demo_mode:
        raise HTTPException(status_code=400, detail="Demo modunda gerçek görev tetiklenemez")
    from app.api.main import hub_activity_worker

    try:
        return await hub_activity_worker.run_once()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/agents")
async def list_agent_cards() -> JSONResponse:
    hub = get_investment_hub()
    cards = hub.list_identity_cards(_mesh().list_agents())
    return JSONResponse([c.model_dump() for c in cards])


@router.get("/agents/{agent_id}")
async def get_agent_card(agent_id: str) -> JSONResponse:
    hub = get_investment_hub()
    manifest = _mesh().registry.get(agent_id)
    reliability = manifest.reliability_score if manifest else 1.0
    card = hub.build_identity_card(agent_id, reliability)
    if card is None:
        raise HTTPException(status_code=404, detail="Ajan bulunamadı")
    return JSONResponse(card.model_dump())


@router.get("/discovery")
async def hub_discovery_catalog() -> Dict[str, Any]:
    """A2A / x402 Bazaar / Agentic.Market keşif kataloğu."""
    hub = get_investment_hub()
    agents = _mesh().list_agents()
    return build_discovery_catalog(hub, agents)


@router.get("/partnership/info")
async def partnership_info() -> Dict[str, Any]:
    """Pasif ortaklık modeli — rakiplerden fark."""
    return {
        "mode": "passive_partnership",
        "tagline": "Dijital işçiye ortak ol — sen çalıştırma, mesh 7/24 çalışsın",
        "revenue_split": get_investment_hub().split.model_dump(),
        "differentiators": {
            "vs_virtuals": "Gelir iş çıktısından; token spekülasyonu değil",
            "vs_olas_pearl": "Agent'ı siz çalıştırmazsınız — pasif USDC stake",
            "vs_agentbazaar": "Yatırımcı katmanı + %65 gelir havuzu",
            "vs_bittensor": "Subnet alpha bahsi değil; görev geliri payı",
        },
        "how_it_works": [
            "USDC ile işçi havuzuna stake edin",
            "Mesh orchestrator agent'ı 7/24 çalıştırır",
            "Her görev geliri %65 staking havuzuna akar",
            "Payınıza düşen ödülü claim edin",
        ],
    }


@router.post("/partnership/stake")
async def passive_partnership_stake(request: PassiveStakeRequest) -> Dict[str, Any]:
    """Pasif ortaklık stake — Olas Pearl'den fark: agent çalıştırma gerekmez."""
    result = await stake(
        StakeRequest(
            investor_id=request.investor_id,
            agent_id=request.agent_id,
            amount_usdc=request.amount_usdc,
            asset=request.asset,
            tx_hash=request.tx_hash,
        )
    )
    result["partnership_mode"] = request.partnership_mode.value
    result["message"] = (
        "Pasif ortaklık aktif — mesh işçiniz sizin adınıza çalışıyor. "
        "Gelir payı görev tamamlandıkça havuza akar."
    )
    return result


@router.post("/revenue/x402")
async def ingest_x402_revenue(
    request: X402RevenueRequest,
    x_hub_signature: str | None = Header(default=None, alias="X-Hub-Signature"),
) -> Dict[str, Any]:
    """x402 / harici USDC ödemelerini gelir defterine işler."""
    if not settings.x402_enabled:
        raise HTTPException(status_code=503, detail="x402 gelir kanalı kapalı")
    if not verify_webhook_secret(x_hub_signature):
        raise HTTPException(status_code=401, detail="Geçersiz webhook imzası")

    try:
        payment = parse_x402_payment(request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    mesh = _mesh()
    manifest = mesh.registry.get(payment["agent_id"])
    if manifest is None:
        raise HTTPException(status_code=404, detail="Ajan kayıtlı değil")

    hub = get_investment_hub()
    hub.record_external_revenue(
        manifest,
        payment["task_id"],
        payment["amount_usdc"],
        tx_hash=payment.get("tx_hash"),
        payer=payment.get("payer"),
    )
    event = hub.revenue.list_events(agent_id=payment["agent_id"], limit=1)[-1]
    return {
        "recorded": True,
        "agent_id": payment["agent_id"],
        "gross_usd": event.gross_usd,
        "staking_usd": event.staking_usd,
        "source": event.source.value,
        "tx_hash": event.tx_hash,
    }


@router.get("/x402/services")
async def x402_services_catalog() -> Dict[str, Any]:
    """x402 ödenebilir hizmet kataloğu."""
    if not settings.x402_enabled:
        raise HTTPException(status_code=503, detail="x402 kapalı")
    return list_x402_services()


@router.get("/x402/market-pulse")
async def x402_market_pulse_discover(symbol: str = Query(default="bitcoin")) -> Dict[str, Any]:
    """Market-Pulse x402 keşif — ödeme gereksinimleri."""
    if not settings.x402_enabled:
        raise HTTPException(status_code=503, detail="x402 kapalı")
    return {
        "service": "market-pulse",
        "agent_id": MARKET_PULSE_AGENT_ID,
        "real_data": True,
        "data_source": "coingecko",
        "price_usdc": market_pulse_price_usd(),
        "symbol": symbol,
        "payment_required": build_payment_required("market-pulse", context_label=symbol),
        "analyze": {
            "method": "POST",
            "url": f"{settings.public_base_url.rstrip('/')}/hub/x402/market-pulse/analyze",
            "headers_without_payment": "402 Payment Required",
            "headers_with_payment": "X-Payment-Proof veya X-PAYMENT",
        },
    }


@router.post("/x402/market-pulse/analyze")
async def x402_market_pulse_analyze(
    request: MarketPulseAnalyzeRequest,
    x_payment: str | None = Header(default=None, alias="X-PAYMENT"),
    x_payment_proof: str | None = Header(default=None, alias="X-Payment-Proof"),
) -> Any:
    """
    Gerçek Market-Pulse analizi — x402 ödeme zorunlu.
    Ödeme yoksa HTTP 402 + accepts döner.
    """
    if not settings.x402_enabled:
        raise HTTPException(status_code=503, detail="x402 kapalı")

    symbol = request.symbol
    proof_header = x_payment_proof if settings.x402_dev_accept_proof else None

    try:
        proof = parse_payment_proof(
            x_payment,
            proof_header,
            required_usd=market_pulse_price_usd(),
        )
    except PaymentRequiredError:
        return JSONResponse(
            status_code=402,
            content=build_payment_required("market-pulse", context_label=symbol),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    mesh = _mesh()
    manifest = mesh.registry.get(MARKET_PULSE_AGENT_ID)
    if manifest is None:
        raise HTTPException(status_code=404, detail="Market-Pulse kayıtlı değil")

    try:
        result = await fetch_market_snapshot_async(symbol)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"CoinGecko hatası: {exc}") from exc

    hub = get_investment_hub()
    task_id = f"x402_{proof['payment_id']}"
    hub.record_external_revenue(
        manifest,
        task_id,
        proof["amount_usdc"],
        tx_hash=proof.get("tx_hash"),
        payer=proof.get("payer"),
    )
    event = hub.revenue.list_events(agent_id=MARKET_PULSE_AGENT_ID, limit=1)[-1]

    return {
        "paid": True,
        "payment": proof,
        "analysis": result,
        "revenue": {
            "gross_usd": event.gross_usd,
            "staking_usd": event.staking_usd,
            "source": event.source.value,
            "task_id": task_id,
        },
        "message": "Gerçek CoinGecko verisi — x402 ödeme kaydedildi, staking havuzuna aktarıldı",
    }


@router.get("/x402/sentiment-radar")
async def x402_sentiment_radar_discover(
    text: str = Query(default="Bitcoin ETF inflows rise while macro risk stays elevated"),
) -> Dict[str, Any]:
    if not settings.x402_enabled:
        raise HTTPException(status_code=503, detail="x402 kapalı")
    preview = text.strip()[:120]
    return {
        "service": "sentiment-radar",
        "agent_id": SENTIMENT_RADAR_AGENT_ID,
        "real_data": True,
        "data_source": "alternative.me+fng+lexicon",
        "price_usdc": sentiment_radar_price_usd(),
        "text_preview": preview,
        "payment_required": build_payment_required("sentiment-radar", context_label=preview[:40]),
        "analyze": {
            "method": "POST",
            "url": f"{settings.public_base_url.rstrip('/')}/hub/x402/sentiment-radar/analyze",
            "headers_without_payment": "402 Payment Required",
            "headers_with_payment": "X-Payment-Proof veya X-PAYMENT",
        },
    }


@router.post("/x402/sentiment-radar/analyze")
async def x402_sentiment_radar_analyze(
    request: SentimentRadarAnalyzeRequest,
    x_payment: str | None = Header(default=None, alias="X-PAYMENT"),
    x_payment_proof: str | None = Header(default=None, alias="X-Payment-Proof"),
) -> Any:
    if not settings.x402_enabled:
        raise HTTPException(status_code=503, detail="x402 kapalı")

    text = request.text.strip()
    proof_header = x_payment_proof if settings.x402_dev_accept_proof else None

    try:
        proof = parse_payment_proof(
            x_payment,
            proof_header,
            required_usd=sentiment_radar_price_usd(),
        )
    except PaymentRequiredError:
        return JSONResponse(
            status_code=402,
            content=build_payment_required("sentiment-radar", context_label=text[:40]),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    mesh = _mesh()
    manifest = mesh.registry.get(SENTIMENT_RADAR_AGENT_ID)
    if manifest is None:
        raise HTTPException(status_code=404, detail="Sentiment-Radar kayıtlı değil")

    try:
        result = await fetch_sentiment_snapshot_async(text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Sentiment API hatası: {exc}") from exc

    hub = get_investment_hub()
    task_id = f"x402_{proof['payment_id']}"
    hub.record_external_revenue(
        manifest,
        task_id,
        proof["amount_usdc"],
        tx_hash=proof.get("tx_hash"),
        payer=proof.get("payer"),
    )
    event = hub.revenue.list_events(agent_id=SENTIMENT_RADAR_AGENT_ID, limit=1)[-1]

    return {
        "paid": True,
        "payment": proof,
        "analysis": result,
        "revenue": {
            "gross_usd": event.gross_usd,
            "staking_usd": event.staking_usd,
            "source": event.source.value,
            "task_id": task_id,
        },
        "message": "Gerçek Fear&Greed + metin sentiment — x402 ödeme kaydedildi",
    }


def _record_mesh_proof_revenue(
    hub: Any,
    mesh: OpenAgentMeshRouter,
    proof_id: str,
    amount_usdc: float,
    payer: str | None,
) -> List[Dict[str, Any]]:
    """Pipeline gelirini 3 gerçek işçiye eşit böler."""
    share = round(amount_usdc / len(MESH_PROOF_AGENTS), 8)
    recorded: List[Dict[str, Any]] = []
    for index, agent_id in enumerate(MESH_PROOF_AGENTS):
        manifest = mesh.registry.get(agent_id)
        if manifest is None:
            continue
        task_id = f"x402_{proof_id}_{index}"
        hub.record_external_revenue(
            manifest,
            task_id,
            share,
            payer=payer,
        )
        event = hub.revenue.list_events(agent_id=agent_id, limit=1)[-1]
        recorded.append(
            {
                "agent_id": agent_id,
                "gross_usd": event.gross_usd,
                "staking_usd": event.staking_usd,
                "task_id": task_id,
            }
        )
    return recorded


@router.get("/proof/mesh")
async def mesh_proof_discover(symbol: str = Query(default="bitcoin")) -> Dict[str, Any]:
    """Mesh Kanıtı — skeptiklere cevap: 3 gerçek işçi pipeline keşfi."""
    if not settings.x402_enabled:
        raise HTTPException(status_code=503, detail="x402 kapalı")
    return {
        "service": "mesh-proof",
        "tagline": "Mock yok. Simülasyon yok. 3 gerçek API, 1 pipeline.",
        "workers": ["Web-Crawler-Pro", "Sentiment-Radar", "Market-Pulse"],
        "pipeline": "web-crawl → sentiment → market-pulse",
        "price_usdc": mesh_proof_price_usd(),
        "symbol": symbol,
        "real_data": True,
        "payment_required": build_mesh_proof_payment_required(symbol=symbol),
        "run": {
            "method": "POST",
            "url": f"{settings.public_base_url.rstrip('/')}/hub/proof/mesh/run",
            "headers_without_payment": "402 Payment Required",
            "headers_with_payment": "X-Payment-Proof veya X-PAYMENT",
        },
        "curl_demo": (
            f"curl -X POST {settings.public_base_url.rstrip('/')}/hub/proof/mesh/run "
            "-H 'Content-Type: application/json' -H 'X-Payment-Proof: ...' "
            f"-d '{{\"symbol\":\"{symbol}\"}}'"
        ),
    }


@router.post("/proof/mesh/run")
async def mesh_proof_run(
    request: MeshProofRunRequest,
    x_payment: str | None = Header(default=None, alias="X-PAYMENT"),
    x_payment_proof: str | None = Header(default=None, alias="X-Payment-Proof"),
) -> Any:
    """
    OAM Mesh Kanıtı — ödeme sonrası 3 gerçek işçi ardışık çalışır.
    Rakiplerin mock vitrinine karşı: crawl + sentiment + market tek yanıtta.
    """
    if not settings.x402_enabled:
        raise HTTPException(status_code=503, detail="x402 kapalı")

    proof_header = x_payment_proof if settings.x402_dev_accept_proof else None
    try:
        payment = parse_payment_proof(
            x_payment,
            proof_header,
            required_usd=mesh_proof_price_usd(),
        )
    except PaymentRequiredError:
        return JSONResponse(
            status_code=402,
            content=build_mesh_proof_payment_required(symbol=request.symbol),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        result = await run_mesh_proof_pipeline(symbol=request.symbol, url=request.url)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Mesh kanıt hatası: {exc}") from exc

    hub = get_investment_hub()
    mesh = _mesh()
    revenue_rows = _record_mesh_proof_revenue(
        hub,
        mesh,
        result["proof_id"],
        payment["amount_usdc"],
        payment.get("payer"),
    )
    total_staking = sum(row["staking_usd"] for row in revenue_rows)

    vault = get_proof_vault()
    stored = vault.store(
        result,
        paid_usdc=payment["amount_usdc"],
        staking_usdc=total_staking,
        payer=payment.get("payer"),
    )
    base = settings.public_base_url.rstrip("/")

    return {
        "paid": True,
        "payment": payment,
        "proof": result,
        "share": {
            "proof_id": stored.proof_id,
            "json": f"{base}/hub/proof/share/{stored.proof_id}",
            "card": f"{base}/hub/proof/share/{stored.proof_id}/card",
        },
        "revenue": {
            "gross_usd": payment["amount_usdc"],
            "staking_usd": round(total_staking, 6),
            "splits": revenue_rows,
            "source": "x402",
        },
        "message": result["message"],
    }


@router.get("/proof/recent")
async def mesh_proof_recent(limit: int = Query(default=12, ge=1, le=50)) -> Dict[str, Any]:
    """Son mesh kanıtları — vitrin / skeptik listesi."""
    vault = get_proof_vault()
    return {
        "proofs": vault.list_recent(limit),
        "stats": vault.stats(),
    }


@router.get("/proof/share/{proof_id}")
async def mesh_proof_share(proof_id: str) -> Dict[str, Any]:
    record = get_proof_vault().get(proof_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Kanıt bulunamadı")
    return record.to_public()


@router.get("/proof/share/{proof_id}/card", response_class=HTMLResponse)
async def mesh_proof_share_card(proof_id: str) -> HTMLResponse:
    record = get_proof_vault().get(proof_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Kanıt bulunamadı")
    html = render_proof_share_card(record, base_url=settings.public_base_url)
    return HTMLResponse(
        content=html,
        headers={"Cache-Control": "no-store", "X-Hub-Build": HUB_BUILD},
    )


@router.get("/ecosystem")
async def hub_ecosystem_status() -> Dict[str, Any]:
    """Kurucu ajanlar + büyüyen mesh durumu."""
    try:
        growth = get_growth_protocol()
    except RuntimeError:
        from app.agents.founder_bootstrap import bootstrap_full_agents
        from app.api.main import peer_discovery

        bootstrap_full_agents(_mesh(), peer_discovery)
        growth = get_growth_protocol()
    return growth.ecosystem_status()


@router.get("/ecosystem/events")
async def hub_ecosystem_events(limit: int = Query(default=30, ge=1, le=100)) -> Dict[str, Any]:
    try:
        growth = get_growth_protocol()
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Ekosistem henüz başlatılmadı")
    return {"events": growth.list_events(limit)}


@router.post("/ecosystem/join")
async def hub_ecosystem_join(request: EcosystemJoinRequest) -> Dict[str, Any]:
    """Yeni ajan mesh'e katılır — operatör / büyüme."""
    try:
        growth = get_growth_protocol()
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Ekosistem henüz başlatılmadı")
    return growth.join_agent(request.manifest)


@router.post("/ecosystem/hire")
async def hub_ecosystem_hire(request: EcosystemHireRequest) -> Dict[str, Any]:
    """Koordinatör ajanları işe alır."""
    try:
        growth = get_growth_protocol()
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Ekosistem henüz başlatılmadı")
    try:
        return await growth.hire_agents(
            pipeline=request.pipeline,
            goal=request.goal,
            initial_data=request.initial_data,
            symbol=request.symbol,
            url=request.url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/stats")
async def hub_public_stats() -> Dict[str, Any]:
    """Landing / vitrin için canlı metrikler."""
    hub = get_investment_hub()
    agents = _mesh().list_agents()
    cards = hub.list_identity_cards(agents)
    total_revenue = sum(c.finance.total_revenue_usd for c in cards)
    vault_stats = get_proof_vault().stats()
    from app.workers.registry import LIVE_WORKER_IDS

    ecosystem = {}
    try:
        ecosystem = {
            "founders": get_growth_protocol().ecosystem_status().get("founder_count", 0),
            "growth_agents": get_growth_protocol().ecosystem_status().get("growth_count", 0),
        }
    except RuntimeError:
        ecosystem = {}

    return {
        "hub_build": HUB_BUILD,
        "live_workers": len(LIVE_WORKER_IDS),
        "total_agents": len(cards),
        "ecosystem": ecosystem,
        "total_revenue_usd": round(total_revenue, 4),
        "mesh_proofs": vault_stats,
        "x402_services": len(list_x402_services().get("services", [])),
        "tagline": "Ajanlar sistemi kurar · Mock yok · Büyüyen mesh",
    }


@router.get("/revenue/config")
async def revenue_config() -> RevenueSplitConfig:
    return get_investment_hub().split


@router.get("/revenue/events")
async def revenue_events(agent_id: str | None = None, limit: int = 50) -> JSONResponse:
    events = get_investment_hub().revenue.list_events(agent_id=agent_id, limit=limit)
    return JSONResponse([e.model_dump() for e in events])


@router.get("/pools")
async def list_pools() -> JSONResponse:
    pools = get_investment_hub().pools.list_pools()
    return JSONResponse([p.model_dump() for p in pools])


@router.post("/stake")
async def stake(request: StakeRequest) -> Dict[str, Any]:
    hub = get_investment_hub()
    manifest = _mesh().registry.get(request.agent_id)
    if manifest is None:
        raise HTTPException(status_code=404, detail="Ajan kayıtlı değil")
    hub.ensure_agent(manifest)

    onchain = settings.onchain_enabled and is_onchain_ready()
    if onchain and settings.onchain_require_tx:
        if not request.tx_hash:
            raise HTTPException(
                status_code=400,
                detail="On-chain stake için önce MetaMask ile işlemi onaylayın (tx_hash gerekli)",
            )
        try:
            verify_stake_tx(request.tx_hash, request.investor_id, request.agent_id, request.amount_usdc)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        position = hub.pools.stake(
            request.investor_id,
            request.agent_id,
            request.amount_usdc,
            tx_hash=request.tx_hash,
            onchain=onchain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    ledger = hub.pools.list_ledger(request.agent_id, limit=1)
    return {
        "staked": True,
        "onchain": onchain,
        "shares": position.shares,
        "staked_usdc": position.staked_usdc,
        "token_price": hub.pools.token_price(request.agent_id),
        "tx_hash": ledger[-1].tx_hash if ledger else request.tx_hash,
    }


@router.post("/unstake")
async def unstake(request: UnstakeRequest) -> Dict[str, Any]:
    hub = get_investment_hub()
    try:
        usdc_out = hub.pools.unstake(request.investor_id, request.agent_id, request.shares)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"unstaked": True, "usdc_returned": usdc_out}


@router.post("/claim")
async def claim_rewards(request: ClaimRewardsRequest) -> Dict[str, Any]:
    onchain = settings.onchain_enabled and is_onchain_ready()
    claimed_override: float | None = None
    if onchain and settings.onchain_require_tx:
        if not request.tx_hash:
            raise HTTPException(
                status_code=400,
                detail="On-chain claim için MetaMask işlem hash'i gerekli",
            )
        try:
            proof = verify_claim_tx(request.tx_hash, request.investor_id, request.agent_id)
            claimed_override = proof["claimed_usdc"]
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    claimed = get_investment_hub().pools.claim_rewards(
        request.investor_id,
        request.agent_id,
        tx_hash=request.tx_hash,
        claimed_override=claimed_override,
    )
    return {"claimed_usdc": claimed, "onchain": onchain, "tx_hash": request.tx_hash}


@router.get("/positions/{investor_id}")
async def list_positions(investor_id: str) -> JSONResponse:
    positions = get_investment_hub().pools.list_positions(investor_id)
    return JSONResponse([p.model_dump() for p in positions])
