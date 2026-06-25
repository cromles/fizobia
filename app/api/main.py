from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, Optional

from fastapi import FastAPI, HTTPException, Query

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
from app.matching.factory import matcher_backend_name
from app.planning.factory import planner_backend_name
from app.registry.factory import create_registry, registry_backend_name

router_mesh = OpenAgentMeshRouter()
peer_discovery = create_discovery()
discovery_sync = create_discovery_sync(peer_discovery, router_mesh.registry)


@asynccontextmanager
async def lifespan(_: FastAPI):
    router_mesh.registry = create_registry()
    global peer_discovery, discovery_sync
    peer_discovery = create_discovery()
    discovery_sync = create_discovery_sync(peer_discovery, router_mesh.registry)
    discovery_sync.sync_once()
    await discovery_sync.start()
    yield
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


@app.get("/health")
async def health() -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "status": "ok",
        "protocol": "OAM",
        "registry": registry_backend_name(router_mesh.registry),
        "discovery": discovery_backend_name(peer_discovery),
        "planner": planner_backend_name(router_mesh.plan_compiler.decomposer),
        "matcher": matcher_backend_name(router_mesh.matcher),
    }
    ping = getattr(router_mesh.registry, "ping", None)
    if callable(ping):
        payload["registry_alive"] = ping()
    discovery_ping = getattr(peer_discovery, "ping", None)
    if callable(discovery_ping):
        payload["discovery_alive"] = discovery_ping()
    return payload


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


@app.get("/agents", response_model=list[AgentManifest])
async def list_agents() -> list[AgentManifest]:
    return router_mesh.list_agents()


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

    @agent_app.post("/execute")
    async def execute(payload: Dict[str, Any]) -> Dict[str, Any]:
        capability = payload.get("capability")
        data = payload.get("data", {})
        handler = handlers.get(capability)
        if handler is None:
            raise HTTPException(status_code=404, detail=f"Unknown capability: {capability}")
        return handler(data)

    return agent_app
