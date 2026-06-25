from __future__ import annotations

import os
from dataclasses import dataclass


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

    @classmethod
    def from_env(cls) -> OAMSettings:
        port = int(os.getenv("OAM_GATEWAY_PORT", "8787"))
        host = os.getenv("OAM_GATEWAY_HOST", "0.0.0.0")
        public_base = os.getenv("OAM_PUBLIC_BASE_URL", f"http://127.0.0.1:{port}")
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
        )

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_api_key)


settings = OAMSettings.from_env()
