from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable

from app.protocol.schemas import AgentCapability, AgentManifest
from app.registry.agent_registry import RegisteredCapability

_TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)

_SYNONYMS = {
    "analiz": {"analyze", "analysis", "synthesize", "synthesizer", "summary", "sentez"},
    "veri": {"data", "fetch", "fetcher", "extract", "scrape"},
    "özet": {"summary", "summarize", "synthesizer", "sentez"},
    "sentez": {"synthesize", "synthesizer", "summary", "analiz"},
    "çek": {"fetch", "scrape", "extract", "data_fetcher"},
    "fetch": {"data_fetcher", "çek", "scrape"},
}


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_PATTERN.findall(text) if len(token) > 2]


def _expand_tokens(tokens: Iterable[str]) -> set[str]:
    expanded = set(tokens)
    for token in list(expanded):
        expanded.update(_SYNONYMS.get(token, set()))
    return expanded


def _term_frequency(tokens: Iterable[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for token in tokens:
        counts[token] += 1
    total = sum(counts.values()) or 1
    return Counter({token: count / total for token, count in counts.items()})


def cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    shared = set(left.keys()) & set(right.keys())
    dot = sum(left[token] * right[token] for token in shared)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


class SemanticCapabilityMatcher:
    """
    Yetenek eşleştirme katmanı.
    Üretimde embedding servisi ile değiştirilebilir; şimdilik deterministik TF-IDF benzeri skor.
    """

    def score_need_to_capability(self, need: str, capability: AgentCapability) -> float:
        need_tokens = _expand_tokens(tokenize(need))
        cap_text = f"{capability.name} {capability.description}"
        cap_tokens = _expand_tokens(tokenize(cap_text))

        if need.lower() == capability.name.lower():
            return 1.0
        if need.lower() in capability.name.lower():
            return 0.9

        need_vec = _term_frequency(need_tokens)
        cap_vec = _term_frequency(cap_tokens)
        semantic = cosine_similarity(need_vec, cap_vec)

        overlap = len(need_tokens & cap_tokens) / max(len(need_tokens), 1)
        return min(1.0, semantic * 0.7 + overlap * 0.3)

    def score_goal_to_capability(
        self,
        user_goal: str,
        capability: AgentCapability,
        manifest: AgentManifest,
    ) -> float:
        base = self.score_need_to_capability(user_goal, capability)
        trust_weight = 0.85 + (manifest.reliability_score * 0.15)
        cost_penalty = 1.0 / (1.0 + manifest.cost_per_token)
        return min(1.0, base * trust_weight * cost_penalty)

    def find_best_capability(
        self,
        need: str,
        capabilities: list[RegisteredCapability],
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
            score = self.score_goal_to_capability(need, item.capability, manifest)
            if score <= 0.05:
                continue
            if best is None or score > best[1]:
                best = (item, score)
        return best
