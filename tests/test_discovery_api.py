import pytest
from fastapi.testclient import TestClient

from app.api import main as api_main
from app.agents.builtins import FETCHER_MANIFEST
from app.discovery.memory_dht import InMemoryPeerDiscovery
from app.discovery.sync import DiscoverySync
from app.registry.agent_registry import InMemoryAgentRegistry


@pytest.fixture
def client():
    api_main.router_mesh.registry = InMemoryAgentRegistry()
    api_main.peer_discovery = InMemoryPeerDiscovery()
    api_main.discovery_sync = DiscoverySync(
        api_main.peer_discovery,
        api_main.router_mesh.registry,
        interval=0,
    )
    return TestClient(api_main.app)


def test_discovery_announce_and_list(client):
    response = client.post(
        "/discovery/announce",
        json={"manifest": FETCHER_MANIFEST.model_dump(), "ttl": 120},
    )
    assert response.status_code == 200
    peers = client.get("/discovery/peers").json()
    assert len(peers) == 1
    assert peers[0]["agent_id"] == FETCHER_MANIFEST.agent_id


def test_discovery_find_by_capability(client):
    client.post(
        "/discovery/announce",
        json={"manifest": FETCHER_MANIFEST.model_dump(), "ttl": 120},
    )
    peers = client.get("/discovery/peers", params={"capability": "data_fetcher"}).json()
    assert len(peers) == 1


def test_discovery_sync_endpoint(client):
    client.post(
        "/discovery/announce",
        json={"manifest": FETCHER_MANIFEST.model_dump(), "ttl": 120},
    )
    api_main.router_mesh.registry = InMemoryAgentRegistry()
    api_main.discovery_sync.registry = api_main.router_mesh.registry
    response = client.post("/discovery/sync")
    assert response.status_code == 200
    assert response.json()["synced"] == 1
    agents = client.get("/agents").json()
    assert len(agents) == 1
