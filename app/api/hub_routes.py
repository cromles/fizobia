from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse

from app.api.hub_dashboard import render_hub_dashboard
from app.config import settings
from app.core.router import OpenAgentMeshRouter
from app.investment.factory import get_investment_hub
from app.investment.live import build_live_snapshot
from app.investment.schemas import (
    ClaimRewardsRequest,
    RevenueSplitConfig,
    StakeRequest,
    UnstakeRequest,
)
from app.protocol.schemas import AgentManifest

HUB_BUILD = "2026.06.25-real-integration"

router = APIRouter(prefix="/hub", tags=["The Hub"])


def _mesh() -> OpenAgentMeshRouter:
    from app.api.main import router_mesh

    return router_mesh


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def hub_dashboard() -> HTMLResponse:
    hub = get_investment_hub()
    mesh = _mesh()
    agents = mesh.list_agents()
    cards = hub.list_identity_cards(agents)
    manifests = {m.agent_id: m for m in agents}
    html = render_hub_dashboard(
        cards, hub.split, manifests, build=HUB_BUILD, demo_mode=settings.hub_demo_mode
    )
    return HTMLResponse(
        content=html,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "X-Hub-Build": HUB_BUILD,
        },
    )


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
    try:
        position = hub.pools.stake(request.investor_id, request.agent_id, request.amount_usdc)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    ledger = hub.pools.list_ledger(request.agent_id, limit=1)
    return {
        "staked": True,
        "shares": position.shares,
        "staked_usdc": position.staked_usdc,
        "token_price": hub.pools.token_price(request.agent_id),
        "tx_hash": ledger[-1].tx_hash if ledger else None,
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
    claimed = get_investment_hub().pools.claim_rewards(request.investor_id, request.agent_id)
    return {"claimed_usdc": claimed}


@router.get("/positions/{investor_id}")
async def list_positions(investor_id: str) -> JSONResponse:
    positions = get_investment_hub().pools.list_positions(investor_id)
    return JSONResponse([p.model_dump() for p in positions])
