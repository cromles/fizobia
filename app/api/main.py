from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, Optional

from fastapi import FastAPI, HTTPException, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from app.api.hub_routes import router as hub_router
from app.agents.founder_bootstrap import bootstrap_full_agents, bootstrap_founder_agents
from app.core.router import OpenAgentMeshRouter
from app.discovery.factory import create_discovery, create_discovery_sync, discovery_backend_name
from app.protocol.schemas import (
    AgentManifest,
    AnnounceRequest,
    CompilePlanRequest,
    ExecutionPlan,
    RegisterAgentRequest,
    RunGoalRequest,
)
from app.config import settings
from app.matching.factory import matcher_backend_name
from app.network.factory import (
    get_global_mesh,
    get_public_discovery,
    get_signaling_hub,
    get_tunnel_hub,
)
from app.network.schemas import PublicAnnounceRequest, SignalMessage, StunConfigResponse
from app.planning.factory import planner_backend_name
from app.registry.factory import create_registry, registry_backend_name

from app.investment.activity_worker import HubActivityWorker

router_mesh = OpenAgentMeshRouter()
hub_activity_worker = HubActivityWorker(router_mesh)
peer_discovery = create_discovery()
discovery_sync = create_discovery_sync(peer_discovery, router_mesh.registry)
global_mesh = get_global_mesh()
signaling_hub = get_signaling_hub()
tunnel_hub = get_tunnel_hub()
public_discovery = get_public_discovery()


@asynccontextmanager
async def lifespan(_: FastAPI):
    router_mesh.registry = create_registry()
    global peer_discovery, discovery_sync
    peer_discovery = create_discovery()
    discovery_sync = create_discovery_sync(peer_discovery, router_mesh.registry)
    stack_mode = os.getenv("OAM_STACK_MODE", "full").lower()
    if stack_mode == "founder":
        bootstrap_founder_agents(router_mesh, peer_discovery)
    else:
        bootstrap_full_agents(router_mesh, peer_discovery)
    discovery_sync.sync_once()
    await discovery_sync.start()
    await hub_activity_worker.start()
    yield
    await hub_activity_worker.stop()
    await discovery_sync.stop()
    registry = router_mesh.registry
    if hasattr(registry, "close"):
        registry.close()
    if hasattr(peer_discovery, "close"):
        peer_discovery.close()


app = FastAPI(
    title="Open Agent Mesh",
    description="Dağıtık yapay zeka ajanları için TCP/IP benzeri orkestrasyon protokolü",
    version="0.1.0",
    lifespan=lifespan,
)
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
app.include_router(hub_router)


@app.get("/.well-known/agent.json")
async def well_known_agent() -> Dict[str, Any]:
    from app.investment.discovery_export import build_platform_agent_card

    return build_platform_agent_card()


@app.get("/.well-known/mpp.json")
async def well_known_mpp() -> Dict[str, Any]:
    from app.investment.discovery_export import build_mpp_descriptor

    return build_mpp_descriptor()


@app.get("/health")
async def health() -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "status": "ok",
        "protocol": "OAM",
        "service": "open-agent-mesh",
        "version": "0.1.0",
        "registry": registry_backend_name(router_mesh.registry),
        "discovery": discovery_backend_name(peer_discovery),
        "planner": planner_backend_name(router_mesh.plan_compiler.decomposer),
        "matcher": matcher_backend_name(router_mesh.matcher),
        "sandbox": getattr(router_mesh.sandbox, "backend_name", "unknown"),
        "network": global_mesh.stun_config().get("protocol", "OAM-NAT-v2"),
        "hub": "/hub",
        "revenue_split": {
            "staking": "65%",
            "platform": "10%",
            "operator": "25%",
        },
        "signaling_peers": len(signaling_hub.connected_peers),
        "tunnel_peers": len(tunnel_hub.connected_peers),
        "public_peers": len(public_discovery.list_network_records()),
        "webrtc": global_mesh.webrtc.available,
    }
    ping = getattr(router_mesh.registry, "ping", None)
    if callable(ping):
        payload["registry_alive"] = ping()
    discovery_ping = getattr(peer_discovery, "ping", None)
    if callable(discovery_ping):
        payload["discovery_alive"] = discovery_ping()
    return payload


@app.get("/", response_class=HTMLResponse)
async def dashboard() -> str:
    agents = router_mesh.list_agents()
    peers = peer_discovery.list_peers()
    rows = ""
    for agent in agents:
        caps = ", ".join(c.name for c in agent.capabilities)
        rows += f"""
        <tr>
          <td><code>{agent.agent_id}</code></td>
          <td><a href="{agent.endpoint}">{agent.endpoint}</a></td>
          <td>{caps}</td>
          <td>{agent.reliability_score:.2f}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="utf-8"/>
  <title>Open Agent Mesh</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; background: #0f172a; color: #e2e8f0; }}
    h1 {{ color: #38bdf8; }}
  a {{ color: #7dd3fc; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
    th, td {{ border: 1px solid #334155; padding: 0.6rem; text-align: left; }}
    th {{ background: #1e293b; }}
    .badge {{ background: #065f46; padding: 0.2rem 0.5rem; border-radius: 4px; }}
    code {{ background: #1e293b; padding: 0.1rem 0.3rem; border-radius: 3px; }}
  </style>
</head>
<body>
  <h1>Open Agent Mesh <span class="badge">OAM</span></h1>
  <p>Registry: <strong>{len(agents)}</strong> ajan · DHT: <strong>{len(peers)}</strong> peer</p>
  <p>
    <a href="/hub">The Hub</a> ·
    <a href="/agents">/agents</a> (JSON) ·
    <a href="/network/stun">/network/stun</a> ·
    <a href="/network/peers">/network/peers</a> ·
    <a href="/health">/health</a> ·
    <a href="/docs">/docs</a>
  </p>
  <table>
    <thead><tr><th>Ajan ID</th><th>Endpoint</th><th>Yetenekler</th><th>Güven</th></tr></thead>
    <tbody>{rows or '<tr><td colspan="4">Henüz ajan yok</td></tr>'}</tbody>
  </table>
</body>
</html>"""


@app.get("/agents")
async def list_agents() -> JSONResponse:
    return JSONResponse([a.model_dump() for a in router_mesh.list_agents()])


@app.post("/agents/register", response_model=Dict[str, Any])
async def register_agent(
    request: RegisterAgentRequest,
    upsert: bool = Query(default=False),
) -> Dict[str, Any]:
    if upsert:
        router_mesh.upsert_agent(request.manifest)
        return {"agent_id": request.manifest.agent_id, "registered": True, "upserted": True}
    accepted = router_mesh.register_agent(request.manifest)
    if not accepted:
        raise HTTPException(status_code=409, detail="Agent already registered")
    return {"agent_id": request.manifest.agent_id, "registered": True}


@app.post("/discovery/announce")
async def announce_peer(request: AnnounceRequest) -> Dict[str, Any]:
    peer_discovery.announce(request.manifest, ttl=request.ttl)
    router_mesh.upsert_agent(request.manifest)
    return {
        "announced": True,
        "agent_id": request.manifest.agent_id,
        "ttl": request.ttl,
    }


@app.get("/discovery/peers", response_model=list[AgentManifest])
async def list_discovered_peers(
    capability: Optional[str] = Query(default=None),
) -> list[AgentManifest]:
    if capability:
        return peer_discovery.find_by_capability(capability)
    return peer_discovery.list_peers()


@app.post("/discovery/sync")
async def sync_discovery() -> Dict[str, Any]:
    count = discovery_sync.sync_once()
    return {"synced": count}


@app.get("/network/stun", response_model=StunConfigResponse)
async def network_stun_config() -> StunConfigResponse:
    config = global_mesh.stun_config()
    return StunConfigResponse(**config)


@app.post("/network/announce")
async def network_public_announce(request: PublicAnnounceRequest) -> Dict[str, Any]:
    record = global_mesh.register_public_peer(request)
    router_mesh.upsert_agent(record.manifest)
    peer_discovery.announce(record.manifest, ttl=request.ttl)
    return {
        "announced": True,
        "agent_id": record.agent_id,
        "local_endpoint": record.local_endpoint,
        "public_endpoint": record.public_endpoint,
        "reachable_endpoint": record.manifest.endpoint,
        "tunnel_active": tunnel_hub.is_connected(record.agent_id),
    }


@app.get("/network/peers")
async def network_public_peers() -> JSONResponse:
    records = public_discovery.list_network_records()
    return JSONResponse([r.model_dump() for r in records])


@app.websocket("/network/signal/{peer_id}")
async def network_signal(websocket: WebSocket, peer_id: str) -> None:
    await signaling_hub.connect(peer_id, websocket)
    try:
        while True:
            raw = await websocket.receive_json()
            message = SignalMessage.model_validate(raw)
            if message.type.value == "ping":
                await websocket.send_json(
                    SignalMessage(
                        type=message.type,
                        from_peer="gateway",
                        to_peer=peer_id,
                        payload={"status": "ok"},
                    ).model_dump()
                )
                continue
            result = await global_mesh.handle_incoming_signal(message)
            if result is not None:
                await websocket.send_json({"type": "signal_result", "payload": result})
            await signaling_hub.relay(message)
    except Exception:
        await signaling_hub.disconnect(peer_id)


@app.websocket("/network/tunnel/{peer_id}")
async def network_tunnel(websocket: WebSocket, peer_id: str) -> None:
    async def on_register(agent_id: str, message: Dict[str, Any]) -> None:
        manifest_data = message.get("manifest")
        if not manifest_data:
            return
        manifest = AgentManifest.model_validate(manifest_data)
        record = global_mesh.register_tunnel_peer(
            agent_id=agent_id,
            local_endpoint=message.get("local_endpoint", manifest.endpoint),
            manifest=manifest,
        )
        router_mesh.upsert_agent(record.manifest)
        peer_discovery.announce(record.manifest, ttl=300)

    await tunnel_hub.listen(peer_id, websocket, on_register=on_register)


@app.post("/network/webrtc/handshake/{peer_id}")
async def network_webrtc_handshake(peer_id: str) -> Dict[str, Any]:
    offer = await global_mesh.initiate_webrtc_handshake(peer_id)
    if "error" in offer:
        raise HTTPException(status_code=503, detail=offer["error"])
    return offer


@app.post("/plans/compile", response_model=ExecutionPlan)
async def compile_plan(request: CompilePlanRequest) -> ExecutionPlan:
    try:
        return await router_mesh.compile_plan(request.user_goal, request.initial_data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/plans/execute")
async def execute_plan(request: ExecutionPlan) -> Dict[str, Any]:
    try:
        result = await router_mesh.execute_plan_verified(request)
        return result.model_dump()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/mesh/run")
async def run_goal(request: RunGoalRequest) -> Dict[str, Any]:
    try:
        result = await router_mesh.run_goal(request.user_goal, request.initial_data)
        return result.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def create_mock_agent_app(
    agent_id: str,
    handlers: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]],
) -> FastAPI:
    """Tekil ajan endpoint'i — OAM protokolüne uygun /execute yüzeyi."""
    agent_app = FastAPI(title=f"OAM Agent: {agent_id}")

    @agent_app.get("/health")
    async def health() -> Dict[str, str]:
        return {"status": "ok", "agent_id": agent_id}

    @agent_app.post("/execute")
    async def execute(payload: Dict[str, Any]) -> Dict[str, Any]:
        capability = payload.get("capability")
        data = payload.get("data", {})
        handler = handlers.get(capability)
        if handler is None:
            raise HTTPException(status_code=404, detail=f"Unknown capability: {capability}")
        return handler(data)

    return agent_app
