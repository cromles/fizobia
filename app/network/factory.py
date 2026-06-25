from __future__ import annotations

import logging

from app.config import settings
from app.network.nat import NATTraversalCoordinator
from app.network.public_discovery import PublicPeerDiscovery
from app.network.signaling import SignalingHub
from app.sandbox.executor import DockerSandboxExecutor, LocalSandboxExecutor, SandboxExecutor

logger = logging.getLogger(__name__)

_signaling_hub = SignalingHub()
_public_discovery = PublicPeerDiscovery()


def get_signaling_hub() -> SignalingHub:
    return _signaling_hub


def get_public_discovery() -> PublicPeerDiscovery:
    return _public_discovery


def create_nat_coordinator(public_base_url: str | None = None) -> NATTraversalCoordinator:
    base = (public_base_url or settings.public_base_url).rstrip("/")
    return NATTraversalCoordinator(
        discovery=_public_discovery,
        signaling=_signaling_hub,
        public_base_url=base,
    )


def create_sandbox_executor() -> SandboxExecutor:
    if settings.sandbox_backend == "docker":
        logger.info("OAM sandbox backend: docker")
        return DockerSandboxExecutor()
    logger.info("OAM sandbox backend: local")
    return LocalSandboxExecutor()
