from __future__ import annotations

import logging

from redis import Redis

from app.config import settings
from app.registry.agent_registry import AgentRegistry, InMemoryAgentRegistry
from app.registry.redis_registry import RedisAgentRegistry

logger = logging.getLogger(__name__)


def registry_backend_name(registry: AgentRegistry) -> str:
    if isinstance(registry, RedisAgentRegistry):
        return registry.backend_name
    if isinstance(registry, InMemoryAgentRegistry):
        return "memory"
    return registry.__class__.__name__.lower()


def create_registry() -> AgentRegistry:
    if settings.registry_backend == "redis":
        try:
            client = Redis.from_url(settings.redis_url, decode_responses=True)
            client.ping()
            logger.info("OAM registry backend: redis (%s)", settings.redis_url)
            return RedisAgentRegistry(client)
        except Exception as exc:
            logger.warning(
                "Redis bağlantısı kurulamadı, bellek içi registry'ye düşülüyor: %s",
                exc,
            )
    logger.info("OAM registry backend: memory")
    return InMemoryAgentRegistry()
