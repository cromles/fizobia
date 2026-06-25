from typing import Any, Dict, List

import pytest

from app.network.mesh import GlobalNetworkMesh
from app.network.public_discovery import PublicPeerDiscovery
from app.network.signaling import SignalingHub
from app.network.tunnel import TUNNEL_PREFIX, TunnelHub
from app.network.webrtc import WebRTCSessionManager
from app.protocol.schemas import AgentCapability, AgentManifest


class MockWebSocket:
    """TunnelHub testleri için otomatik execute yanıtı üreten sahte WebSocket."""

    def __init__(self, hub: TunnelHub | None = None, agent_id: str = "") -> None:
        self.sent: List[Dict[str, Any]] = []
        self._hub = hub
        self._agent_id = agent_id
        self._closed = False

    async def accept(self) -> None:
        return None

    async def send_json(self, payload: Dict[str, Any]) -> None:
        self.sent.append(payload)
        if (
            self._hub is not None
            and payload.get("type") == "execute"
        ):
            request_id = payload.get("request_id")
            future = self._hub._pending.get(request_id)
            if future and not future.done():
                data = payload.get("data", {})
                if "message" in data:
                    result = {"message": data["message"]}
                else:
                    result = {"message": "via-tunnel"}
                future.set_result(result)

    async def close(self) -> None:
        self._closed = True


def _echo_manifest(agent_id: str = "tunnel.test.agent") -> AgentManifest:
    return AgentManifest(
        agent_id=agent_id,
        endpoint="http://192.168.1.10:9000",
        capabilities=[
            AgentCapability(
                name="echo",
                description="echo",
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
        ],
    )


@pytest.fixture
def mesh() -> GlobalNetworkMesh:
    return GlobalNetworkMesh(
        discovery=PublicPeerDiscovery(),
        signaling=SignalingHub(),
        tunnel=TunnelHub(),
        webrtc=WebRTCSessionManager(),
        public_base_url="http://gateway:8787",
    )


@pytest.mark.asyncio
async def test_tunnel_hub_execute_remote():
    hub = TunnelHub()
    ws = MockWebSocket(hub=hub, agent_id="agent.tunnel")
    await hub.connect("agent.tunnel", ws)

    result = await hub.execute_remote("agent.tunnel", "echo", {"message": "oam"})

    assert result == {"message": "oam"}


@pytest.mark.asyncio
async def test_tunnel_hub_offline_returns_error():
    hub = TunnelHub()
    result = await hub.execute_remote("missing.agent", "echo", {})
    assert "error" in result


def test_mesh_resolve_tunnel_route_when_connected(mesh: GlobalNetworkMesh):
    manifest = _echo_manifest()
    mesh.tunnel._connections["tunnel.test.agent"] = MockWebSocket()  # type: ignore[assignment]
    route = mesh.resolve_route(manifest)
    assert route == {"mode": "tunnel", "target": "tunnel.test.agent"}


def test_mesh_resolve_tunnel_route_from_endpoint_prefix(mesh: GlobalNetworkMesh):
    manifest = _echo_manifest()
    manifest = manifest.model_copy(
        update={"endpoint": f"{TUNNEL_PREFIX}http://gateway:8787/tunnel.test.agent"}
    )
    route = mesh.resolve_route(manifest)
    assert route["mode"] == "tunnel"


def test_register_tunnel_peer_sets_virtual_endpoint(mesh: GlobalNetworkMesh):
    manifest = _echo_manifest()
    record = mesh.register_tunnel_peer(
        agent_id=manifest.agent_id,
        local_endpoint="http://192.168.1.10:9000",
        manifest=manifest,
    )
    assert record.public_endpoint.startswith(TUNNEL_PREFIX)
    assert record.manifest.endpoint.startswith(TUNNEL_PREFIX)
    assert record.nat_type == "tunnel"


@pytest.mark.asyncio
async def test_mesh_execute_via_tunnel(mesh: GlobalNetworkMesh):
    ws = MockWebSocket(hub=mesh.tunnel, agent_id="tunnel.test.agent")
    await mesh.tunnel.connect("tunnel.test.agent", ws)

    manifest = _echo_manifest()
    manifest = manifest.model_copy(
        update={"endpoint": mesh.tunnel.tunnel_endpoint(manifest.agent_id, mesh.public_base_url)}
    )
    result = await mesh.execute(
        manifest=manifest,
        capability="echo",
        data={"message": "via-tunnel"},
        http_executor=lambda *args, **kwargs: {"error": "http_should_not_run"},
    )
    assert result == {"message": "via-tunnel"}


def test_stun_config_includes_tunnel_and_webrtc(mesh: GlobalNetworkMesh):
    config = mesh.stun_config()
    assert config["protocol"] == "OAM-NAT-v2"
    assert config["tunnel_url"].endswith("/network/tunnel")
    assert "webrtc_available" in config
