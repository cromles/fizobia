import time

import pytest
import fakeredis

from app.discovery.memory_dht import InMemoryPeerDiscovery
from app.discovery.redis_dht import RedisPeerDiscovery
from app.discovery.sync import DiscoverySync
from app.protocol.schemas import AgentCapability, AgentManifest
from app.registry.agent_registry import InMemoryAgentRegistry


def _manifest(agent_id: str = "peer-1") -> AgentManifest:
    return AgentManifest(
        agent_id=agent_id,
        endpoint=f"http://{agent_id}",
        capabilities=[
            AgentCapability(
                name="data_fetcher",
                description="fetch",
                input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"raw_text": {"type": "string"}}},
            )
        ],
    )


def test_memory_dht_announces_and_finds_capability():
    dht = InMemoryPeerDiscovery()
    dht.announce(_manifest(), ttl=60)
    peers = dht.find_by_capability("data_fetcher")
    assert len(peers) == 1
    assert peers[0].agent_id == "peer-1"


def test_memory_dht_expires_stale_peers():
    dht = InMemoryPeerDiscovery()
    dht.announce(_manifest(), ttl=1)
    dht._peers["peer-1"] = (_manifest(), time.time() - 1)
    assert dht.list_peers() == []


def test_discovery_sync_populates_registry():
    dht = InMemoryPeerDiscovery()
    registry = InMemoryAgentRegistry()
    dht.announce(_manifest())
    sync = DiscoverySync(dht, registry, interval=0)
    assert sync.sync_once() == 1
    assert registry.get("peer-1") is not None


def test_redis_dht_roundtrip():
    client = fakeredis.FakeRedis(decode_responses=True)
    dht = RedisPeerDiscovery(client)
    dht.announce(_manifest("redis-peer"))
    peers = dht.find_by_capability("data_fetcher")
    assert peers[0].agent_id == "redis-peer"
