from __future__ import annotations

import json
import logging
import re
from typing import List, Optional, Protocol

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.registry.agent_registry import RegisteredCapability

logger = logging.getLogger(__name__)


class GoalDecomposer(Protocol):
    backend_name: str

    async def extract_capability_needs(
        self,
        user_goal: str,
        capabilities: Optional[List[RegisteredCapability]] = None,
    ) -> List[str]: ...


class DecomposerResponse(BaseModel):
    steps: List[str] = Field(default_factory=list)


class DeterministicGoalDecomposer:
    """Anahtar kelime ve sinonim tabanlı deterministik hedef ayrıştırıcı."""

    backend_name = "deterministic"

    _GOAL_HINTS = (
        ("data_fetcher", ("çek", "fetch", "scrape", "indir", "kaynak", "veri", "web")),
        ("synthesizer", ("sentez", "özet", "analiz", "synthesize", "summary", "rapor")),
        ("transform", ("dönüştür", "transform", "parse", "çevir", "normalize")),
    )

    async def extract_capability_needs(
        self,
        user_goal: str,
        capabilities: Optional[List[RegisteredCapability]] = None,
    ) -> List[str]:
        goal_lower = user_goal.lower()
        known_names = {item.capability.name for item in (capabilities or [])}
        needs: List[str] = []

        for capability_hint, keywords in self._GOAL_HINTS:
            if capability_hint in known_names and any(
                keyword in goal_lower for keyword in keywords
            ):
                needs.append(capability_hint)
            elif not known_names and any(keyword in goal_lower for keyword in keywords):
                needs.append(capability_hint)

        if not needs and capabilities:
            for item in capabilities:
                cap = item.capability
                cap_text = f"{cap.name} {cap.description}".lower()
                if any(token in cap_text for token in goal_lower.split() if len(token) > 3):
                    needs.append(cap.name)

        if not needs:
            needs.append(user_goal)

        downstream = {"synthesizer", "transform"}
        if any(need in downstream for need in needs) and "data_fetcher" not in needs:
            if not known_names or "data_fetcher" in known_names:
                needs.insert(0, "data_fetcher")
        return needs


class LLMGoalDecomposer:
    """
    OpenAI uyumlu chat API ile hedefi yetenek zincirine çevirir.
    Yalnızca ağda kayıtlı capability adlarını döndürmesi için prompt kısıtlıdır.
    """

    backend_name = "llm"

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _build_prompt(
        self,
        user_goal: str,
        capabilities: List[RegisteredCapability],
    ) -> str:
        catalog = "\n".join(
            f"- {item.capability.name}: {item.capability.description}"
            for item in capabilities
        )
        return (
            "Sen Open Agent Mesh planlayıcısısın. Kullanıcı hedefini tamamlamak için "
            "gerekli capability adlarını SIRALI JSON listesi olarak döndür.\n"
            "Sadece aşağıdaki kayıtlı capability adlarını kullan.\n"
            "Başka açıklama yazma, yalnızca JSON ver.\n\n"
            f"Kayıtlı capability'ler:\n{catalog or '- (boş)'}\n\n"
            f"Kullanıcı hedefi: {user_goal}\n\n"
            'JSON formatı: {"steps": ["capability_a", "capability_b"]}'
        )

    @staticmethod
    def _parse_steps(content: str) -> List[str]:
        content = content.strip()
        try:
            payload = json.loads(content)
            return DecomposerResponse.model_validate(payload).steps
        except (json.JSONDecodeError, ValidationError):
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if match:
                payload = json.loads(match.group())
                return DecomposerResponse.model_validate(payload).steps
            raise

    def _sanitize_steps(
        self,
        steps: List[str],
        capabilities: List[RegisteredCapability],
    ) -> List[str]:
        allowed = {item.capability.name for item in capabilities}
        sanitized = [step for step in steps if step in allowed]
        return sanitized

    async def extract_capability_needs(
        self,
        user_goal: str,
        capabilities: Optional[List[RegisteredCapability]] = None,
    ) -> List[str]:
        if not self.available:
            raise RuntimeError("LLM API anahtarı yapılandırılmamış")
        if not capabilities:
            raise RuntimeError("LLM planlayıcı için kayıtlı capability gerekli")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": "OAM görev planlayıcısısın. Yalnızca geçerli JSON döndür.",
                },
                {
                    "role": "user",
                    "content": self._build_prompt(user_goal, capabilities),
                },
            ],
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=body,
            )
            response.raise_for_status()
            payload = response.json()

        content = payload["choices"][0]["message"]["content"]
        steps = self._sanitize_steps(self._parse_steps(content), capabilities)
        if not steps:
            raise RuntimeError("LLM geçerli capability zinciri üretemedi")
        logger.info("LLM planlayıcı zincir üretti: %s", steps)
        return steps


class HybridGoalDecomposer:
    """LLM planlayıcı; hata veya yapılandırma eksikliğinde deterministik fallback."""

    backend_name = "hybrid"

    def __init__(
        self,
        llm: LLMGoalDecomposer,
        fallback: Optional[DeterministicGoalDecomposer] = None,
    ) -> None:
        self.llm = llm
        self.fallback = fallback or DeterministicGoalDecomposer()

    async def extract_capability_needs(
        self,
        user_goal: str,
        capabilities: Optional[List[RegisteredCapability]] = None,
    ) -> List[str]:
        if self.llm.available and capabilities:
            try:
                return await self.llm.extract_capability_needs(user_goal, capabilities)
            except Exception as exc:
                logger.warning("LLM planlayıcı başarısız, deterministik fallback: %s", exc)
        return await self.fallback.extract_capability_needs(user_goal, capabilities)
