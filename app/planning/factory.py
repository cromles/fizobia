from __future__ import annotations

import logging

from app.config import settings
from app.matching.embedding_matcher import EmbeddingCapabilityMatcher, HybridCapabilityMatcher
from app.matching.semantic_matcher import SemanticCapabilityMatcher
from app.planning.decomposer import (
    DeterministicGoalDecomposer,
    GoalDecomposer,
    HybridGoalDecomposer,
    LLMGoalDecomposer,
)

logger = logging.getLogger(__name__)


def create_decomposer() -> GoalDecomposer:
    llm = LLMGoalDecomposer(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
    )
    deterministic = DeterministicGoalDecomposer()

    if settings.planner_backend == "llm":
        logger.info("OAM planner backend: llm")
        return llm
    if settings.planner_backend == "deterministic":
        logger.info("OAM planner backend: deterministic")
        return deterministic

    logger.info("OAM planner backend: hybrid")
    return HybridGoalDecomposer(llm=llm, fallback=deterministic)


def planner_backend_name(decomposer: GoalDecomposer) -> str:
    return getattr(decomposer, "backend_name", decomposer.__class__.__name__.lower())
