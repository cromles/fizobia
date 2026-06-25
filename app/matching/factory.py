from __future__ import annotations

import logging

from app.config import settings
from app.matching.embedding_matcher import EmbeddingCapabilityMatcher, HybridCapabilityMatcher
from app.matching.semantic_matcher import SemanticCapabilityMatcher

logger = logging.getLogger(__name__)


def create_matcher() -> SemanticCapabilityMatcher | HybridCapabilityMatcher:
    semantic = SemanticCapabilityMatcher()
    embedding = EmbeddingCapabilityMatcher(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.embedding_model,
        fallback=semantic,
    )

    if settings.matcher_backend == "embedding":
        logger.info("OAM matcher backend: embedding")
        return embedding
    if settings.matcher_backend == "deterministic":
        logger.info("OAM matcher backend: deterministic")
        return semantic

    logger.info("OAM matcher backend: hybrid")
    return HybridCapabilityMatcher(embedding=embedding, fallback=semantic)


def matcher_backend_name(matcher: object) -> str:
    return getattr(matcher, "backend_name", matcher.__class__.__name__.lower())
