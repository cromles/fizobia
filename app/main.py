"""OAM örnek ajanları ve mesh gateway başlatıcıları."""

import uvicorn

from app.agents.builtins import (
    FETCHER_MANIFEST,
    MOCK_HANDLERS,
    SYNTHESIZER_MANIFEST,
    TRANSFORMER_MANIFEST,
)
from app.api.main import app, create_mock_agent_app, router_mesh


def bootstrap_default_mesh() -> None:
    for manifest in (FETCHER_MANIFEST, SYNTHESIZER_MANIFEST, TRANSFORMER_MANIFEST):
        router_mesh.register_agent(manifest)


def run_gateway(host: str = "0.0.0.0", port: int = 8000) -> None:
    bootstrap_default_mesh()
    uvicorn.run(app, host=host, port=port)


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
