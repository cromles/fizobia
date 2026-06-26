"""OAM örnek ajanları ve mesh gateway başlatıcıları."""

import os
from typing import Any, Dict

import uvicorn

from app.agents.bootstrap import bootstrap_default_agents
from app.agents.builtins import (
    FETCHER_MANIFEST,
    MOCK_HANDLERS,
    SYNTHESIZER_MANIFEST,
    TRANSFORMER_MANIFEST,
)
from app.api.main import app, create_mock_agent_app, router_mesh
from app.config import settings
from app.registry.factory import create_registry
from app.discovery.factory import create_discovery


def bootstrap_default_mesh() -> None:
    mode = os.getenv("OAM_STACK_MODE", "full").lower()
    router_mesh.registry = create_registry()
    if mode in ("founder", "ecosystem"):
        # Lifespan doğru bootstrap'ı yapar — burada sadece boş registry
        return
    discovery = create_discovery()
    bootstrap_default_agents(router_mesh, discovery)


def run_gateway(
    host: str | None = None,
    port: int | None = None,
) -> None:
    bootstrap_default_mesh()
    uvicorn.run(
        app,
        host=host or settings.gateway_host,
        port=port or settings.gateway_port,
    )


def run_mock_fetcher() -> None:
    uvicorn.run(
        create_mock_agent_app("oam.fetcher.local", {"data_fetcher": MOCK_HANDLERS["data_fetcher"]}),
        host="127.0.0.1",
        port=8101,
    )


def run_mock_synthesizer() -> None:
    uvicorn.run(
        create_mock_agent_app(
            "oam.synthesizer.local", {"synthesizer": MOCK_HANDLERS["synthesizer"]}
        ),
        host="127.0.0.1",
        port=8102,
    )


def run_mock_transformer() -> None:
    uvicorn.run(
        create_mock_agent_app("oam.transformer.local", {"transform": MOCK_HANDLERS["transform"]}),
        host="127.0.0.1",
        port=8103,
    )


def run_extended_agent(agent_id: str, port: int, handlers: Dict[str, Any]) -> None:
    uvicorn.run(
        create_mock_agent_app(agent_id, handlers),
        host="127.0.0.1",
        port=port,
    )


def run_extended_agents() -> None:
    """Tek process'te tüm genişletilmiş ajanları başlatır (geliştirme kısayolu)."""
    from app.agents.extended_builtins import EXTENDED_HANDLERS, EXTENDED_MANIFESTS

    manifest = EXTENDED_MANIFESTS[0]
    port = int(manifest.endpoint.rsplit(":", 1)[-1])
    handlers = EXTENDED_HANDLERS.get(manifest.agent_id, {})
    run_extended_agent(manifest.agent_id, port, handlers)


if __name__ == "__main__":
    run_gateway()
