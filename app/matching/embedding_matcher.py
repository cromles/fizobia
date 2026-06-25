from __future__ import annotations

import logging
import math
from typing import Dict, List, Optional

import httpx

from app.matching.semantic_matcher import SemanticCapabilityMatcher
from app.protocol.schemas import AgentCapability, AgentManifest
from app.registry.agent_registry import RegisteredCapability

logger = logging.getLogger(__name__)


class EmbeddingCapabilityMatcher:
    """
    OpenAI uyumlu embedding API ile semantik yetenek eşleştirme.
    Deterministik matcher'a göre doğal dil hedeflerinde daha isabetli sonuç verir.
    """

    backend_name = "embedding"

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "text-embedding-3-small",
        timeout: float = 20.0,
        fallback: Optional[SemanticCapabilityMatcher] = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.fallback = fallback or SemanticCapabilityMatcher()
        self._cache: Dict[str, List[float]] = {}

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def _embed(self, text: str) -> List[float]:
        if text in self._cache:
            return self._cache[text]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {"model": self.model, "input": text}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json=body,
            )
            response.raise_for_status()
            vector = response.json()["data"][0]["embedding"]

        self._cache[text] = vector
        return vector

    @staticmethod
    def _vector_cosine(left: List[float], right: List[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        dot = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return dot / (left_norm * right_norm)

    def _capability_text(self, capability: AgentCapability) -> str:
        return f"{capability.name}. {capability.description}"

    async def score_need_to_capability_async(
        self,
        need: str,
        capability: AgentCapability,
    ) -> float:
        if not self.available:
            return self.fallback.score_need_to_capability(need, capability)

        need_vec = await self._embed(need)
        cap_vec = await self._embed(self._capability_text(capability))
        semantic = self._vector_cosine(need_vec, cap_vec)
        lexical = self.fallback.score_need_to_capability(need, capability)
        return min(1.0, semantic * 0.75 + lexical * 0.25)

    def score_need_to_capability(self, need: str, capability: AgentCapability) -> float:
        return self.fallback.score_need_to_capability(need, capability)

    def score_goal_to_capability(
        self,
        user_goal: str,
        capability: AgentCapability,
        manifest: AgentManifest,
    ) -> float:
        base = self.fallback.score_goal_to_capability(user_goal, capability, manifest)
        return base

    async def score_goal_to_capability_async(
        self,
        user_goal: str,
        capability: AgentCapability,
        manifest: AgentManifest,
    ) -> float:
        base = await self.score_need_to_capability_async(user_goal, capability)
        trust_weight = 0.85 + (manifest.reliability_score * 0.15)
        cost_penalty = 1.0 / (1.0 + manifest.cost_per_token)
        return min(1.0, base * trust_weight * cost_penalty)

    async def find_best_capability_async(
        self,
        need: str,
        capabilities: List[RegisteredCapability],
    ) -> tuple[RegisteredCapability, float] | None:
        best: tuple[RegisteredCapability, float] | None = None
        for item in capabilities:
            manifest = AgentManifest(
                agent_id=item.agent_id,
                endpoint=item.endpoint,
                reliability_score=item.reliability_score,
                cost_per_token=item.cost_per_token,
                capabilities=[item.capability],
            )
            if self.available:
                score = await self.score_goal_to_capability_async(
                    need, item.capability, manifest
                )
            else:
                score = self.fallback.score_goal_to_capability(
                    need, item.capability, manifest
                )
            if score <= 0.05:
                continue
            if best is None or score > best[1]:
                best = (item, score)
        return best

    def find_best_capability(
        self,
        need: str,
        capabilities: List[RegisteredCapability],
    ) -> tuple[RegisteredCapability, float] | None:
        return self.fallback.find_best_capability(need, capabilities)


class HybridCapabilityMatcher:
    """Embedding + deterministik skorların birleşimi; API yoksa otomatik fallback."""

    backend_name = "hybrid"

    def __init__(
        self,
        embedding: EmbeddingCapabilityMatcher,
        fallback: Optional[SemanticCapabilityMatcher] = None,
    ) -> None:
        self.embedding = embedding
        self.fallback = fallback or SemanticCapabilityMatcher()

    def score_need_to_capability(self, need: str, capability: AgentCapability) -> float:
        return self.fallback.score_need_to_capability(need, capability)

    def score_goal_to_capability(
        self,
        user_goal: str,
        capability: AgentCapability,
        manifest: AgentManifest,
    ) -> float:
        return self.fallback.score_goal_to_capability(user_goal, capability, manifest)

    async def score_goal_to_capability_async(
        self,
        user_goal: str,
        capability: AgentCapability,
        manifest: AgentManifest,
    ) -> float:
        if self.embedding.available:
            return await self.embedding.score_goal_to_capability_async(
                user_goal, capability, manifest
            )
        return self.fallback.score_goal_to_capability(user_goal, capability, manifest)

    async def find_best_capability_async(
        self,
        need: str,
        capabilities: List[RegisteredCapability],
    ) -> tuple[RegisteredCapability, float] | None:
        if self.embedding.available:
            return await self.embedding.find_best_capability_async(need, capabilities)
        return self.fallback.find_best_capability(need, capabilities)

    def find_best_capability(
        self,
        need: str,
        capabilities: List[RegisteredCapability],
    ) -> tuple[RegisteredCapability, float] | None:
        return self.fallback.find_best_capability(need, capabilities)
