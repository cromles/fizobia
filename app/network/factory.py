from __future__ import annotations

import logging

from app.config import settings
from app.network.mesh import GlobalNetworkMesh
from app.network.nat import NATTraversalCoordinator
from app.network.public_discovery import PublicPeerDiscovery
from app.network.signaling import SignalingHub
from app.network.tunnel import TunnelHub
from app.network.webrtc import WebRTCSessionManager
from app.sandbox.executor import DockerSandboxExecutor, LocalSandboxExecutor, SandboxExecutor

logger = logging.getLogger(__name__)

_signaling_hub = SignalingHub()
_tunnel_hub = TunnelHub()
_public_discovery = PublicPeerDiscovery()
_webrtc_manager = WebRTCSessionManager()
_global_mesh: GlobalNetworkMesh | None = None


def get_signaling_hub() -> SignalingHub:
    return _signaling_hub


def get_tunnel_hub() -> TunnelHub:
    return _tunnel_hub


def get_public_discovery() -> PublicPeerDiscovery:
    return _public_discovery


def get_webrtc_manager() -> WebRTCSessionManager:
    return _webrtc_manager


def get_global_mesh() -> GlobalNetworkMesh:
    global _global_mesh
    if _global_mesh is None:
        _global_mesh = GlobalNetworkMesh(
            discovery=_public_discovery,
            signaling=_signaling_hub,
            tunnel=_tunnel_hub,
            webrtc=_webrtc_manager,
            public_base_url=settings.public_base_url,
        )
    return _global_mesh


def create_nat_coordinator(public_base_url: str | None = None) -> NATTraversalCoordinator:
    """Geriye uyumluluk — GlobalNetworkMesh üzerinden koordinatör."""
    mesh = get_global_mesh()
    if public_base_url:
        mesh.public_base_url = public_base_url.rstrip("/")
    return NATTraversalCoordinator(
        discovery=mesh.discovery,
        signaling=mesh.signaling,
        public_base_url=mesh.public_base_url,
    )


def create_sandbox_executor() -> SandboxExecutor:
    if settings.sandbox_backend == "docker":
        logger.info("OAM sandbox backend: docker")
        return DockerSandboxExecutor()
    logger.info("OAM sandbox backend: local")
    return LocalSandboxExecutor()
