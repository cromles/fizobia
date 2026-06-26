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
    verify_unstake_tx,
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
    arena_price_usd,
    build_arena_payment_required,
    build_mesh_proof_payment_required,
    build_payment_required,
    list_x402_services,
    market_pulse_price_usd,
    mesh_proof_price_usd,
    parse_payment_proof,
    sentiment_radar_price_usd,
)
from app.mesh.arena_pipeline import run_arena_pipeline
from app.mesh.article_pipeline import run_article_pipeline
from app.mesh.agent_wallets import credit_agent, list_ledger, list_wallets, record_loss
from app.mesh.proof_pipeline import MESH_PROOF_AGENTS, run_mesh_proof_pipeline
from app.mesh.growth_protocol import get_growth_protocol
from app.mesh.agent_dialogue import get_dialogue_bus
from app.mesh.mission import get_mission_status
from app.mesh.hierarchy import (
    announce_chain_of_command,
    get_hierarchy_status,
    record_founder_command,
)
from app.mesh.organism import get_organism_status
from app.mesh.proof_vault import get_proof_vault
from app.api.hub_ui.proof_card import render_proof_share_card
from app.protocol.schemas import AgentCapability, AgentManifest
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
    tx_hash: str | None = Field(default=None, description="Opsiyonel USDC tx doğrulama")


class UserPromptRequest(BaseModel):
    prompt: str = Field(..., min_length=8, max_length=4000, description="Tek girdi — doğal dil istem")
    background_music: bool = Field(default=True)
    duration_sec: int = Field(default=30, ge=15, le=90)


class ArticleRequest(BaseModel):
    topic: str = Field(..., min_length=8, max_length=4000, description="Makale konusu")
    tone: str = Field(default="corporate", description="corporate | humorous | technical")
    url: str | None = Field(default=None, description="Opsiyonel RSS/HTML kaynağı")


class EcosystemJoinRequest(BaseModel):
    manifest: AgentManifest


class EcosystemAssembleRequest(BaseModel):
    symbol: str = Field(default="bitcoin")
    url: str | None = None


class EcosystemHireRequest(BaseModel):
    pipeline: str = Field(
        default="mesh_proof",
        description="mesh_proof | ecosystem_assembly | goal | arena | article",
    )
    goal: str = Field(default="")
    initial_data: Dict[str, Any] = Field(default_factory=dict)
    symbol: str = Field(default="bitcoin")
    url: str | None = None
    tx_hash: str | None = None


class AgentDialogueRequest(BaseModel):
    from_agent: str
    to_agent: str
    text: str
    intent: str = Field(default="inform")
    payload: Dict[str, Any] = Field(default_factory=dict)
    thread_id: str | None = None


class FounderCommandRequest(BaseModel):
    command: str = Field(default="accelerate", description="accelerate | mesh_proof | custom")
    message: str = Field(default="Durma, hızlan — ne gerekiyorsa yap.")
    payload: Dict[str, Any] = Field(default_factory=dict)


HUB_BUILD = "2026.06.26-departments-v18"

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
    brand_title: str = "Axium",
    brand_sub: str = "Financial AI Terminal",
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
            "user_prompt": f"{base}/hub/prompt",
            "arena_wallets": f"{base}/hub/arena/wallets",
            "leaderboard": f"{base}/hub/leaderboard",
            "departments": f"{base}/hub/departments",
            "article": f"{base}/hub/article",
            "ecosystem": f"{base}/hub/ecosystem",
            "ecosystem_join": f"{base}/hub/ecosystem/join",
            "ecosystem_hire": f"{base}/hub/ecosystem/hire",
            "ecosystem_events": f"{base}/hub/ecosystem/events",
            "ecosystem_dialogue": f"{base}/hub/ecosystem/dialogue",
            "ecosystem_mission": f"{base}/hub/ecosystem/mission",
            "hierarchy": f"{base}/hub/hierarchy",
            "hierarchy_command": f"{base}/hub/hierarchy/command",
            "autopilot": f"{base}/hub/autopilot",
            "ecosystem_assemble": f"{base}/hub/ecosystem/assemble",
            "manifest": f"{base}/hub/manifest",
            "organism": f"{base}/hub/organism",
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


    return recorded


def _minimal_arena_manifest(agent_id: str, display_name: str) -> AgentManifest:
    schema = {"type": "object", "properties": {"prompt": {"type": "string"}}}
    return AgentManifest(
        agent_id=agent_id,
        endpoint=f"local://{agent_id}",
        capabilities=[
            AgentCapability(
                name="arena_worker",
                description=display_name,
                input_schema=schema,
                output_schema=schema,
            )
        ],
    )


def _arena_payout_amounts(gross_usdc: float) -> Dict[str, float]:
    """$0.10 referans: metin kazanan %10, render %40, kasa %50."""
    return {
        "text_winner": round(gross_usdc * 0.10, 6),
        "render": round(gross_usdc * 0.40, 6),
        "treasury": round(gross_usdc * 0.50, 6),
    }


def _record_arena_payouts(
    hub: Any,
    mesh: OpenAgentMeshRouter,
    result: Dict[str, Any],
    gross_usdc: float,
    payer: str | None,
) -> Dict[str, Any]:
    from app.workers.media_render import AGENT_ID as RENDER_ID, DISPLAY_NAME as RENDER_NAME

    job_id = result["job_id"]
    splits = _arena_payout_amounts(gross_usdc)
    payouts: List[Dict[str, Any]] = []

    winner_id = result.get("winner", {}).get("agent_id", "")
    winner_name = result.get("winner", {}).get("display_name", winner_id)
    if winner_id and splits["text_winner"] > 0:
        credit_agent(
            winner_id,
            splits["text_winner"],
            reason="arena_text_winner",
            job_id=job_id,
            payer=payer,
        )
        manifest = mesh.registry.get(winner_id) or _minimal_arena_manifest(winner_id, winner_name)
        hub.record_external_revenue(manifest, f"{job_id}_text", splits["text_winner"], payer=payer)
        payouts.append({"agent_id": winner_id, "role": "text_winner", "usd": splits["text_winner"]})

    for loser_id in result.get("arena", {}).get("mapping", {}).get("loser_agent_ids", []):
        record_loss(loser_id, job_id=job_id)

    if splits["render"] > 0:
        credit_agent(
            RENDER_ID,
            splits["render"],
            reason="arena_render",
            job_id=job_id,
            payer=payer,
        )
        render_manifest = mesh.registry.get(RENDER_ID) or _minimal_arena_manifest(RENDER_ID, RENDER_NAME)
        hub.record_external_revenue(render_manifest, f"{job_id}_render", splits["render"], payer=payer)
        payouts.append({"agent_id": RENDER_ID, "role": "render", "usd": splits["render"]})

    return {
        "gross_usdc": gross_usdc,
        "splits": splits,
        "payouts": payouts,
        "treasury_usd": splits["treasury"],
        "wallet_ledger": list_ledger(job_id=job_id),
    }


@router.get("/prompt")
async def arena_prompt_discover() -> Dict[str, Any]:
    """Tek girdi UX — gladyatör arena keşfi."""
    return {
        "service": "synapse-arena",
        "tagline": "Tek kutu. Arka planda organizma uyanır.",
        "method": "POST",
        "url": f"{settings.public_base_url.rstrip('/')}/hub/prompt",
        "price_usd": arena_price_usd(),
        "pipeline": [
            "paralel metin ajanları (arena)",
            "kör denetim (bağışıklık)",
            "kazanan → Reels render",
            "mikro cüzdan ödemeleri",
        ],
        "demo_free": settings.hub_demo_mode,
    }


@router.post("/prompt")
async def user_prompt_arena(
    request: UserPromptRequest,
    x_payment: str | None = Header(default=None, alias="X-PAYMENT"),
    x_payment_proof: str | None = Header(default=None, alias="X-Payment-Proof"),
) -> Any:
    """
    Tek kullanıcı girdisi — gladyatör arenası.
    Demo modda ücretsiz; canlıda x402 USDC.
    """
    payment: Dict[str, Any] = {"amount_usdc": 0.0, "payer": None, "demo": settings.hub_demo_mode}

    if not settings.hub_demo_mode:
        if not settings.x402_enabled:
            raise HTTPException(status_code=503, detail="x402 kapalı")
        proof_header = x_payment_proof if settings.x402_dev_accept_proof else None
        try:
            payment = parse_payment_proof(
                x_payment,
                proof_header,
                required_usd=arena_price_usd(),
            )
        except PaymentRequiredError:
            return JSONResponse(
                status_code=402,
                content=build_arena_payment_required(prompt_preview=request.prompt),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        result = await run_arena_pipeline(
            user_prompt=request.prompt,
            background_music=request.background_music,
            duration_sec=request.duration_sec,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Arena hatası: {exc}") from exc

    hub = get_investment_hub()
    mesh = _mesh()
    gross = payment["amount_usdc"] if payment["amount_usdc"] > 0 else arena_price_usd()
    revenue = _record_arena_payouts(
        hub,
        mesh,
        result,
        gross,
        payment.get("payer"),
    )

    return {
        "paid": payment["amount_usdc"] > 0,
        "payment": payment,
        "result": result,
        "revenue": revenue,
        "wallets": list_wallets(limit=10),
        "message": result.get("message", "Arena tamamlandı"),
    }


@router.get("/arena/wallets")
async def arena_wallets(limit: int = Query(default=30, ge=1, le=100)) -> Dict[str, Any]:
    """Ajan mikro cüzdanları — görev başına kazanç."""
    return {"wallets": list_wallets(limit=limit)}


@router.get("/departments")
async def hub_departments() -> Dict[str, Any]:
    """Dikey uzmanlık departmanları — yatırım kategorileri ve mikro ajan hücreleri."""
    mesh = _mesh()
    from app.mesh.departments import list_departments

    registered = [m.agent_id for m in mesh.list_agents()]
    return list_departments(registered_agent_ids=registered)


@router.get("/article")
async def article_pipeline_discover() -> Dict[str, Any]:
    """Yazılı basın departmanı — makale mikro-ajan zinciri keşfi."""
    from app.mesh.departments import ARTICLE_PIPELINE_AGENTS, DEPARTMENT_COPYWRITING

    return {
        "service": "synapse-article",
        "department": DEPARTMENT_COPYWRITING,
        "tagline": "Tek makale bile dört ayrı mikro ajan zincirinden geçer.",
        "method": "POST",
        "url": f"{settings.public_base_url.rstrip('/')}/hub/article",
        "hire_url": f"{settings.public_base_url.rstrip('/')}/hub/ecosystem/hire",
        "pipeline": [
            "Web-Crawler (araştırma)",
            "Story-Weaver (taslak)",
            "Brand-Voice (üslup)",
            "Immune-Critic (onay)",
        ],
        "agents": list(ARTICLE_PIPELINE_AGENTS),
        "tones": ["corporate", "humorous", "technical"],
    }


@router.post("/article")
async def article_pipeline_run(request: ArticleRequest) -> Dict[str, Any]:
    """Makale pipeline — copywriting departmanı mikro işçi hücreleri."""
    try:
        result = await run_article_pipeline(
            topic=request.topic,
            tone=request.tone,
            url=request.url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Makale pipeline hatası: {exc}") from exc
    return {"pipeline": "article", "result": result, "real_data": True}


@router.get("/leaderboard")
async def hub_gladiator_leaderboard(
    department_code: str | None = Query(default=None, description="media_video | copywriting | technical"),
) -> Dict[str, Any]:
    """Gladyatör liderlik tablosu — borsa terminali görünümü için."""
    mesh = _mesh()
    hub = get_investment_hub()
    organism = get_organism_status()
    standings_map = {s["agent_id"]: s for s in organism.get("agent_standings", [])}
    wallets_map = {w["agent_id"]: w for w in list_wallets(limit=200)}
    from app.mesh.departments import DEPARTMENTS, departments_for_agent, primary_department

    rows: List[Dict[str, Any]] = []
    for card in hub.list_identity_cards(mesh.list_agents()):
        aid = card.profile.agent_id
        dept = primary_department(aid)
        if department_code and department_code not in departments_for_agent(aid):
            continue
        st = standings_map.get(aid, {})
        wl = wallets_map.get(aid, {})
        wins = int(wl.get("tasks_won", 0))
        losses = int(wl.get("tasks_lost", 0))
        total_tasks = wins + losses
        if total_tasks > 0:
            success_pct = round(100.0 * wins / total_tasks, 1)
        else:
            success_pct = round(float(st.get("score", 0.5)) * 100, 1)

        price = card.finance.token_price_usdc
        dept_spec = DEPARTMENTS.get(dept)
        rows.append(
            {
                "agent_id": aid,
                "display_name": card.profile.display_name,
                "token_symbol": card.profile.token_symbol,
                "success_rate_pct": success_pct,
                "volume_24h_usd": card.finance.volume_24h_usd,
                "token_price_usdc": price,
                "apy_pct": card.finance.estimated_apy,
                "tvl_usd": card.finance.staking_pool_tvl_usd,
                "identity_tier": st.get("identity_tier", "probation"),
                "earned_usdc": wl.get("earned_usdc", 0.0),
                "tier_badge": st.get("identity_tier", "probation"),
                "department_code": dept,
                "department_label": dept_spec.label_short if dept_spec else dept,
                "departments": list(departments_for_agent(aid)),
            }
        )

    rows.sort(key=lambda r: (-r["volume_24h_usd"], -r["success_rate_pct"], -r["tvl_usd"]))
    total_tvl = sum(r["tvl_usd"] for r in rows)
    return {
        "agents": rows,
        "count": len(rows),
        "total_tvl_usd": round(total_tvl, 2),
        "revenue_split_staking_pct": 65,
        "department_filter": department_code,
    }


@router.get("/proof/mesh")
async def mesh_proof_discover(symbol: str = Query(default="bitcoin")) -> Dict[str, Any]:
    """Mesh Kanıtı — skeptiklere cevap: 3 gerçek işçi pipeline keşfi."""
    if not settings.x402_enabled:
        raise HTTPException(status_code=503, detail="x402 kapalı")
    return {
        "service": "mesh-proof",
        "tagline": "Mock yok. 4 gerçek API, ajan diyaloğu, 1 pipeline.",
        "workers": ["Web-Crawler-Pro", "Sentiment-Radar", "Market-Pulse", "On-Chain-Watcher"],
        "pipeline": "web-crawl → sentiment → market → on-chain",
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
        result = await run_mesh_proof_pipeline(
            symbol=request.symbol, url=request.url, tx_hash=request.tx_hash
        )
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
        import os

        from app.api.main import peer_discovery

        mode = os.getenv("OAM_STACK_MODE", "full").lower()
        if mode == "ecosystem":
            from app.agents.ecosystem_bootstrap import bootstrap_ecosystem_agents

            bootstrap_ecosystem_agents(_mesh(), peer_discovery)
        elif mode == "founder":
            from app.agents.founder_bootstrap import bootstrap_founder_agents

            bootstrap_founder_agents(_mesh(), peer_discovery)
        else:
            from app.agents.founder_bootstrap import bootstrap_full_agents

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


@router.post("/ecosystem/assemble")
async def hub_ecosystem_assemble(request: EcosystemAssembleRequest) -> Dict[str, Any]:
    """Tüm ekosistemi bir araya getir — mesh proof + medya + sermaye."""
    try:
        growth = get_growth_protocol()
    except RuntimeError:
        from app.agents.ecosystem_bootstrap import bootstrap_ecosystem_agents
        from app.api.main import peer_discovery

        bootstrap_ecosystem_agents(_mesh(), peer_discovery)
        growth = get_growth_protocol()
    try:
        return await growth.hire_agents(
            pipeline="ecosystem_assembly",
            symbol=request.symbol,
            url=request.url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


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


@router.get("/ecosystem/mission")
async def hub_ecosystem_mission() -> Dict[str, Any]:
    """Axium ailesi ortak misyonu — ajanlara yayınlanan charter."""
    return get_mission_status()


@router.get("/hierarchy")
async def hub_hierarchy() -> Dict[str, Any]:
    """Komuta zinciri — Kurucu → Baş Yardımcı → Koordinatör → İşçiler."""
    return get_hierarchy_status(_mesh().list_agents())


@router.post("/hierarchy/command")
async def hub_hierarchy_command(request: FounderCommandRequest) -> Dict[str, Any]:
    """Kurucu emri — baş yardımcı ve koordinatöre iletilir."""
    order = record_founder_command(
        request.command,
        message=request.message,
        payload=request.payload,
    )
    try:
        growth = get_growth_protocol()
        growth._emit(
            "founder_command",
            f"Kurucu emri: {request.message[:80]}",
            detail=order,
        )
    except RuntimeError:
        pass
    return {"accepted": True, "order": order}


@router.get("/manifest")
async def hub_founder_manifest() -> Dict[str, Any]:
    """Yasin Karademir — kurucu manifestosu, Synapse Net ve büyüme fazları."""
    return get_organism_status()


@router.get("/synapse")
async def hub_synapse_manifest() -> Dict[str, Any]:
    """Synapse Net (Ortak Bilinç) — teknik charter ve mimari katmanlar."""
    from app.mesh.synapse_manifest import get_synapse_manifest

    return get_synapse_manifest()


@router.get("/organism")
async def hub_organism_status() -> Dict[str, Any]:
    """Süper organizma durumu — planlanan bölümler ve ajan kimlikleri."""
    return get_organism_status()


@router.get("/autopilot")
async def hub_autopilot_status() -> Dict[str, Any]:
    """7/24 otopilot döngü durumu."""
    from app.api.main import mesh_autopilot

    return mesh_autopilot.status()


@router.post("/autopilot/run")
async def hub_autopilot_run_once() -> Dict[str, Any]:
    """Tek otopilot döngüsünü hemen çalıştır."""
    if settings.hub_demo_mode:
        raise HTTPException(status_code=400, detail="Demo modunda otopilot çalışmaz")
    from app.api.main import mesh_autopilot

    try:
        return await mesh_autopilot.run_cycle()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/ecosystem/dialogue")
async def hub_ecosystem_dialogue(
    limit: int = Query(default=40, ge=1, le=200),
    thread_id: str | None = None,
    agent_id: str | None = None,
) -> Dict[str, Any]:
    """Ajanlar arası konuşma günlüğü."""
    bus = get_dialogue_bus()
    messages = bus.list_messages(limit=limit, thread_id=thread_id, agent_id=agent_id)
    return {
        "messages": messages,
        "count": len(messages),
        "thread_id": thread_id,
    }


@router.post("/ecosystem/dialogue")
async def hub_ecosystem_dialogue_send(request: AgentDialogueRequest) -> Dict[str, Any]:
    """Ajan → ajan mesaj gönder."""
    bus = get_dialogue_bus()
    msg = bus.say(
        request.from_agent,
        request.to_agent,
        request.text,
        intent=request.intent,
        payload=request.payload,
        thread_id=request.thread_id,
    )
    try:
        growth = get_growth_protocol()
        growth._emit(
            "agent_dialogue",
            f"{request.from_agent} → {request.to_agent}: {request.text[:80]}",
            agent_id=request.from_agent,
            detail=msg.to_public(),
        )
    except RuntimeError:
        pass
    return msg.to_public()


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
    onchain = settings.onchain_enabled and is_onchain_ready()
    usdc_override: float | None = None
    if onchain and settings.onchain_require_tx:
        if not request.tx_hash:
            raise HTTPException(
                status_code=400,
                detail="On-chain unstake için MetaMask işlem hash'i gerekli",
            )
        try:
            proof = verify_unstake_tx(
                request.tx_hash,
                request.investor_id,
                request.agent_id,
                request.shares,
            )
            usdc_override = proof["usdc_returned"]
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        usdc_out = hub.pools.unstake(
            request.investor_id,
            request.agent_id,
            request.shares,
            tx_hash=request.tx_hash,
            usdc_override=usdc_override,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "unstaked": True,
        "usdc_returned": usdc_out,
        "onchain": onchain,
        "tx_hash": request.tx_hash,
    }


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
