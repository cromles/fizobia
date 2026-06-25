from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from fastapi import APIRouter, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse

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
from app.protocol.schemas import AgentManifest

HUB_BUILD = "2026.06.25-nebula-ui"

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
