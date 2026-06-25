from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class OAMSettings:
    registry_backend: str
    redis_url: str
    planner_backend: str
    matcher_backend: str
    llm_api_key: str
    llm_base_url: str
    llm_model: str
    embedding_model: str

    discovery_backend: str
    discovery_sync_interval: float
    gateway_port: int
    gateway_host: str
    public_base_url: str
    sandbox_backend: str
    extra_stun_servers: List[str]
    turn_servers: List[str]
    hub_demo_mode: bool
    hub_live_interval: float
    onchain_enabled: bool
    onchain_require_tx: bool
    onchain_rpc_url: str
    onchain_chain_id: int
    onchain_deployment_file: str
    onchain_operator_key: str

    @classmethod
    def from_env(cls) -> OAMSettings:
        port = int(os.getenv("OAM_GATEWAY_PORT", "8787"))
        host = os.getenv("OAM_GATEWAY_HOST", "0.0.0.0")
        public_base = os.getenv("OAM_PUBLIC_BASE_URL", f"http://127.0.0.1:{port}")
        extra_stun = [
            item.strip()
            for item in os.getenv("OAM_EXTRA_STUN_SERVERS", "").split(",")
            if item.strip()
        ]
        turn_raw = os.getenv("OAM_TURN_SERVERS", "")
        turn_servers = [item.strip() for item in turn_raw.split(",") if item.strip()]
        demo_mode = os.getenv("OAM_HUB_DEMO", "false").lower() in ("1", "true", "yes")
        live_interval = float(os.getenv("OAM_HUB_LIVE_INTERVAL", "30" if not demo_mode else "0"))
        onchain_enabled = os.getenv("OAM_ONCHAIN_ENABLED", "false").lower() in ("1", "true", "yes")
        onchain_require_tx = os.getenv("OAM_ONCHAIN_REQUIRE_TX", "true").lower() in ("1", "true", "yes")
        return cls(
            registry_backend=os.getenv("OAM_REGISTRY_BACKEND", "memory").lower(),
            redis_url=os.getenv("OAM_REDIS_URL", "redis://localhost:6379/0"),
            planner_backend=os.getenv("OAM_PLANNER_BACKEND", "hybrid").lower(),
            matcher_backend=os.getenv("OAM_MATCHER_BACKEND", "hybrid").lower(),
            llm_api_key=os.getenv("OAM_LLM_API_KEY", os.getenv("OPENAI_API_KEY", "")),
            llm_base_url=os.getenv("OAM_LLM_BASE_URL", "https://api.openai.com/v1"),
            llm_model=os.getenv("OAM_LLM_MODEL", "gpt-4o-mini"),
            embedding_model=os.getenv("OAM_EMBEDDING_MODEL", "text-embedding-3-small"),
            discovery_backend=os.getenv("OAM_DISCOVERY_BACKEND", "memory").lower(),
            discovery_sync_interval=float(os.getenv("OAM_DISCOVERY_SYNC_INTERVAL", "30")),
            gateway_port=port,
            gateway_host=host,
            public_base_url=public_base,
            sandbox_backend=os.getenv("OAM_SANDBOX_BACKEND", "local").lower(),
            extra_stun_servers=extra_stun,
            turn_servers=turn_servers,
            hub_demo_mode=demo_mode,
            hub_live_interval=live_interval,
            onchain_enabled=onchain_enabled,
            onchain_require_tx=onchain_require_tx,
            onchain_rpc_url=os.getenv("OAM_ONCHAIN_RPC_URL", "http://127.0.0.1:8545"),
            onchain_chain_id=int(os.getenv("OAM_ONCHAIN_CHAIN_ID", "31337")),
            onchain_deployment_file=os.getenv("OAM_ONCHAIN_DEPLOYMENT", "deployments/local.json"),
            onchain_operator_key=os.getenv("OAM_ONCHAIN_OPERATOR_KEY", ""),
        )

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_api_key)


settings = OAMSettings.from_env()
