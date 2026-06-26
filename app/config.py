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
    hub_autopilot_enabled: bool
    hub_autopilot_interval: float
    hub_autopilot_warmup: float
    hub_autopilot_min_agents: int
    onchain_enabled: bool
    onchain_require_tx: bool
    onchain_rpc_url: str
    onchain_chain_id: int
    onchain_deployment_file: str
    onchain_operator_key: str
    cors_origins: List[str]
    embed_frame_origins: List[str]
    x402_enabled: bool
    x402_webhook_secret: str
    x402_market_pulse_price_usd: float
    x402_sentiment_radar_price_usd: float
    x402_mesh_proof_price_usd: float
    x402_network: str
    x402_payee_address: str
    x402_dev_accept_proof: bool
    x402_rpc_url: str
    x402_usdc_contract: str

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
        autopilot_enabled = os.getenv("OAM_AUTOPILOT_ENABLED", "true").lower() in ("1", "true", "yes")
        autopilot_interval = float(
            os.getenv("OAM_AUTOPILOT_INTERVAL", "90" if not demo_mode else "0")
        )
        autopilot_warmup = float(os.getenv("OAM_AUTOPILOT_WARMUP", "20"))
        autopilot_min_agents = int(os.getenv("OAM_AUTOPILOT_MIN_AGENTS", "3"))
        onchain_enabled = os.getenv("OAM_ONCHAIN_ENABLED", "false").lower() in ("1", "true", "yes")
        onchain_require_tx = os.getenv("OAM_ONCHAIN_REQUIRE_TX", "true").lower() in ("1", "true", "yes")
        cors_raw = os.getenv(
            "OAM_CORS_ORIGINS",
            "https://zinesh.com,https://www.zinesh.com,http://localhost:3000,http://127.0.0.1:3000",
        )
        cors_origins = [o.strip() for o in cors_raw.split(",") if o.strip()]
        embed_raw = os.getenv(
            "OAM_EMBED_FRAME_ORIGINS",
            "https://zinesh.com,https://www.zinesh.com,http://localhost:3000,http://127.0.0.1:3000",
        )
        embed_frame_origins = [o.strip() for o in embed_raw.split(",") if o.strip()]
        x402_enabled = os.getenv("OAM_X402_ENABLED", "true").lower() in ("1", "true", "yes")
        x402_webhook_secret = os.getenv("OAM_X402_WEBHOOK_SECRET", "")
        x402_market_pulse_price_usd = float(os.getenv("OAM_X402_MARKET_PULSE_PRICE", "0.05"))
        x402_sentiment_radar_price_usd = float(os.getenv("OAM_X402_SENTIMENT_PRICE", "0.04"))
        x402_mesh_proof_price_usd = float(os.getenv("OAM_X402_MESH_PROOF_PRICE", "0.10"))
        x402_network = os.getenv("OAM_X402_NETWORK", "base-sepolia")
        x402_payee_address = os.getenv("OAM_X402_PAYEE_ADDRESS", "")
        x402_dev_accept_proof = os.getenv("OAM_X402_DEV_ACCEPT_PROOF", "true").lower() in (
            "1",
            "true",
            "yes",
        )
        x402_rpc_url = os.getenv(
            "OAM_X402_RPC_URL",
            os.getenv("OAM_ONCHAIN_RPC_URL", "https://sepolia.base.org"),
        )
        x402_usdc_contract = os.getenv(
            "OAM_X402_USDC_CONTRACT",
            "0x036CbD53842c5426634e7929541eC2318f3dCF7e",  # Base Sepolia USDC
        )
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
            hub_autopilot_enabled=autopilot_enabled,
            hub_autopilot_interval=autopilot_interval,
            hub_autopilot_warmup=autopilot_warmup,
            hub_autopilot_min_agents=autopilot_min_agents,
            onchain_enabled=onchain_enabled,
            onchain_require_tx=onchain_require_tx,
            onchain_rpc_url=os.getenv("OAM_ONCHAIN_RPC_URL", "http://127.0.0.1:8545"),
            onchain_chain_id=int(os.getenv("OAM_ONCHAIN_CHAIN_ID", "31337")),
            onchain_deployment_file=os.getenv("OAM_ONCHAIN_DEPLOYMENT", "deployments/local.json"),
            onchain_operator_key=os.getenv("OAM_ONCHAIN_OPERATOR_KEY", ""),
            cors_origins=cors_origins,
            embed_frame_origins=embed_frame_origins,
            x402_enabled=x402_enabled,
            x402_webhook_secret=x402_webhook_secret,
            x402_market_pulse_price_usd=x402_market_pulse_price_usd,
            x402_sentiment_radar_price_usd=x402_sentiment_radar_price_usd,
            x402_mesh_proof_price_usd=x402_mesh_proof_price_usd,
            x402_network=x402_network,
            x402_payee_address=x402_payee_address,
            x402_dev_accept_proof=x402_dev_accept_proof,
            x402_rpc_url=x402_rpc_url,
            x402_usdc_contract=x402_usdc_contract,
        )

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_api_key)


settings = OAMSettings.from_env()
