from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, Callable, Dict

from fastapi import FastAPI, HTTPException

from app.core.router import OpenAgentMeshRouter
from app.protocol.schemas import (
    AgentManifest,
    CompilePlanRequest,
    ExecutionPlan,
    RegisterAgentRequest,
    RunGoalRequest,
)
from app.registry.factory import create_registry, registry_backend_name

router_mesh = OpenAgentMeshRouter()


@asynccontextmanager
async def lifespan(_: FastAPI):
    router_mesh.registry = create_registry()
    yield
    registry = router_mesh.registry
    if hasattr(registry, "close"):
        registry.close()


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
    }
    ping = getattr(router_mesh.registry, "ping", None)
    if callable(ping):
        payload["registry_alive"] = ping()
    return payload


@app.post("/agents/register", response_model=Dict[str, Any])
async def register_agent(request: RegisterAgentRequest) -> Dict[str, Any]:
    accepted = router_mesh.register_agent(request.manifest)
    if not accepted:
        raise HTTPException(status_code=409, detail="Agent already registered")
    return {"agent_id": request.manifest.agent_id, "registered": True}


@app.get("/agents", response_model=list[AgentManifest])
async def list_agents() -> list[AgentManifest]:
    return router_mesh.list_agents()


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
