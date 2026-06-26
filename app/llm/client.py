"""OpenAI uyumlu chat API — Groq, OpenRouter, OpenAI destekler."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_MAX_LLM_ATTEMPTS = 3


def llm_public_status() -> Dict[str, Any]:
    """Hub UI / SDK — anahtar sızdırmadan LLM durumu."""
    return {
        "enabled": settings.llm_enabled,
        "provider": _provider_label(settings.llm_base_url),
        "base_url": settings.llm_base_url,
        "default_model": settings.llm_model,
        "fallback_mode": "template" if not settings.llm_enabled else "llm_with_template_fallback",
        "env_keys": ["OAM_LLM_API_KEY", "OPENAI_API_KEY"],
        "cheap_providers": [
            {"name": "Gemini", "base_url": "https://generativelanguage.googleapis.com/v1beta/openai", "model": "gemini-2.0-flash"},
            {"name": "Groq", "base_url": "https://api.groq.com/openai/v1", "model": "llama-3.1-8b-instant"},
            {"name": "OpenRouter", "base_url": "https://openrouter.ai/api/v1", "model": "openai/gpt-4o-mini"},
            {"name": "OpenAI", "base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"},
        ],
    }


def _provider_label(base_url: str) -> str:
    lower = base_url.lower()
    if "generativelanguage.googleapis.com" in lower or "google" in lower:
        return "gemini"
    if "groq" in lower:
        return "groq"
    if "openrouter" in lower:
        return "openrouter"
    if "openai" in lower:
        return "openai"
    return "openai_compatible"


async def chat_completion(
    *,
    system: str,
    user: str,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 900,
    timeout: float = 45.0,
) -> Tuple[str, Dict[str, Any]]:
    """
    OpenAI /chat/completions çağrısı.
    Dönüş: (metin, meta) — meta latency_ms, model, provider içerir.
    """
    if not settings.llm_enabled:
        raise RuntimeError("LLM API anahtarı yapılandırılmamış")

    use_model = model or settings.llm_model
    # Gemini / özel sağlayıcıda arena ajanlarının gpt-* model adlarını geçersiz kıl
    if _provider_label(settings.llm_base_url) == "gemini" and use_model.startswith("gpt-"):
        use_model = settings.llm_model
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    if "openrouter" in settings.llm_base_url.lower():
        headers["HTTP-Referer"] = settings.public_base_url
        headers["X-Title"] = "Axium Hub"

    body: Dict[str, Any] = {
        "model": use_model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }

    import time

    started = time.perf_counter()
    last_error: Optional[Exception] = None
    payload: Dict[str, Any] = {}

    for attempt in range(1, _MAX_LLM_ATTEMPTS + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{settings.llm_base_url.rstrip('/')}/chat/completions",
                    headers=headers,
                    json=body,
                )
                status = getattr(response, "status_code", 200)
                if status in _RETRYABLE_STATUS and attempt < _MAX_LLM_ATTEMPTS:
                    wait = 1.5 * attempt
                    logger.warning(
                        "LLM %s — %s, %ss sonra yeniden (%s/%s)",
                        use_model,
                        status,
                        wait,
                        attempt,
                        _MAX_LLM_ATTEMPTS,
                    )
                    await asyncio.sleep(wait)
                    continue
                response.raise_for_status()
                payload = response.json()
                break
        except httpx.HTTPStatusError as exc:
            last_error = exc
            if exc.response.status_code in _RETRYABLE_STATUS and attempt < _MAX_LLM_ATTEMPTS:
                await asyncio.sleep(1.5 * attempt)
                continue
            raise
        except httpx.RequestError as exc:
            last_error = exc
            if attempt < _MAX_LLM_ATTEMPTS:
                await asyncio.sleep(1.5 * attempt)
                continue
            raise
    else:
        if last_error:
            raise last_error
        raise RuntimeError("LLM yanıt alınamadı")

    latency_ms = round((time.perf_counter() - started) * 1000, 1)
    content = payload["choices"][0]["message"]["content"].strip()
    usage = payload.get("usage") or {}
    meta = {
        "model": use_model,
        "provider": _provider_label(settings.llm_base_url),
        "latency_ms": latency_ms,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "llm": True,
    }
    logger.info("LLM yanıt — %s · %sms · %d karakter", use_model, latency_ms, len(content))
    return content, meta
