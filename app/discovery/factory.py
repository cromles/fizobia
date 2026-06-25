from __future__ import annotations

import logging

from redis import Redis

from app.config import settings
from app.discovery.memory_dht import InMemoryPeerDiscovery
from app.discovery.redis_dht import RedisPeerDiscovery
from app.discovery.sync import DiscoverySync

logger = logging.getLogger(__name__)


def discovery_backend_name(discovery: object) -> str:
    return getattr(discovery, "backend_name", discovery.__class__.__name__.lower())


def create_discovery() -> InMemoryPeerDiscovery | RedisPeerDiscovery:
    if settings.discovery_backend == "redis":
        try:
            client = Redis.from_url(settings.redis_url, decode_responses=True)
            client.ping()
            logger.info("OAM discovery backend: redis (%s)", settings.redis_url)
            return RedisPeerDiscovery(client)
        except Exception as exc:
            logger.warning(
                "Redis discovery bağlantısı kurulamadı, bellek içi DHT'ye düşülüyor: %s",
                exc,
            )
    logger.info("OAM discovery backend: memory")
    return InMemoryPeerDiscovery()


def create_discovery_sync(discovery, registry) -> DiscoverySync:
    return DiscoverySync(
        discovery=discovery,
        registry=registry,
        interval=settings.discovery_sync_interval,
    )
