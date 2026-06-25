#!/usr/bin/env python3
"""Echo ajanını başlatır ve OAM gateway'e canlı bağlar."""

from __future__ import annotations

import asyncio
import logging
import sys
import threading
import time

import uvicorn

from oam_agent import OAMAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("oam.echo.live")

DEFAULT_GATEWAY = "http://127.0.0.1:8000"
HOST = "127.0.0.1"
PORT = 8200

agent = OAMAgent(
    agent_id="example.echo.agent",
    endpoint=f"http://{HOST}:{PORT}",
    cost_per_token=0.0001,
)


@agent.capability(
    name="echo",
    description="Girdiyi olduğu gibi döndürür; canlı mesh test ajanı",
    input_schema={
        "type": "object",
        "properties": {"message": {"type": "string"}},
        "required": ["message"],
    },
    output_schema={
        "type": "object",
        "properties": {"message": {"type": "string"}},
        "required": ["message"],
    },
)
async def echo_handler(data: dict) -> dict:
    return {"message": data.get("message", "")}


def _run_server() -> None:
    uvicorn.run(agent.app, host=HOST, port=PORT, log_level="info")


async def _join_mesh(gateway_url: str) -> None:
    logger.info("Gateway'e bağlanılıyor: %s", gateway_url)
    await agent.join_mesh(gateway_url, announce=True, heartbeat_interval=30.0)
    logger.info("Echo ajanı canlı bağlandı: %s", agent.manifest.agent_id)


def main() -> None:
    gateway_url = (sys.argv[1] if len(sys.argv) > 1 else DEFAULT_GATEWAY).rstrip("/")

    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()
    time.sleep(1.5)

    asyncio.run(_join_mesh(gateway_url))

    logger.info("Echo ajanı dinliyor: http://%s:%s", HOST, PORT)
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Kapatılıyor...")


if __name__ == "__main__":
    main()
