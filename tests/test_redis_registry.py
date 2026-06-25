import pytest
import fakeredis

from app.protocol.schemas import AgentCapability, AgentManifest
from app.registry.factory import create_registry, registry_backend_name
from app.registry.redis_registry import RedisAgentRegistry


def _sample_manifest(agent_id: str = "agent-redis-1") -> AgentManifest:
    return AgentManifest(
        agent_id=agent_id,
        endpoint="http://localhost:9000",
        reliability_score=0.95,
        capabilities=[
            AgentCapability(
                name="echo",
                description="Echo capability",
                input_schema={"type": "object", "properties": {"msg": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"msg": {"type": "string"}}},
            )
        ],
    )


@pytest.fixture
def redis_registry() -> RedisAgentRegistry:
    client = fakeredis.FakeRedis(decode_responses=True)
    return RedisAgentRegistry(client)


def test_redis_register_and_get(redis_registry: RedisAgentRegistry):
    manifest = _sample_manifest()
    assert redis_registry.register(manifest) is True
    assert redis_registry.register(manifest) is False

    loaded = redis_registry.get("agent-redis-1")
    assert loaded is not None
    assert loaded.endpoint == manifest.endpoint


def test_redis_list_capabilities(redis_registry: RedisAgentRegistry):
    redis_registry.register(_sample_manifest())
    caps = redis_registry.list_capabilities()
    assert len(caps) == 1
    assert caps[0].capability.name == "echo"


def test_redis_update_reliability_persists(redis_registry: RedisAgentRegistry):
    redis_registry.register(_sample_manifest())
    redis_registry.update_reliability("agent-redis-1", 0.5)
    assert redis_registry.get("agent-redis-1").reliability_score == 0.5


def test_redis_survives_registry_reconnect():
    client = fakeredis.FakeRedis(decode_responses=True)
    first = RedisAgentRegistry(client)
    first.register(_sample_manifest("persistent-agent"))

    second = RedisAgentRegistry(client)
    manifest = second.get("persistent-agent")
    assert manifest is not None
    assert manifest.agent_id == "persistent-agent"


def test_factory_defaults_to_memory(monkeypatch):
    monkeypatch.delenv("OAM_REGISTRY_BACKEND", raising=False)
    registry = create_registry()
    assert registry_backend_name(registry) == "memory"


def test_factory_falls_back_when_redis_unavailable(monkeypatch):
    monkeypatch.setenv("OAM_REGISTRY_BACKEND", "redis")
    monkeypatch.setenv("OAM_REDIS_URL", "redis://127.0.0.1:1")
    registry = create_registry()
    assert registry_backend_name(registry) == "memory"
