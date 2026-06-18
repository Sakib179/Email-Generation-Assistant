from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from .config import Settings


logger = logging.getLogger(__name__)


class LLMGatewayError(RuntimeError):
    def __init__(self, public_message: str, *, status_code: int | None = None, retry_after_seconds: float | None = None):
        super().__init__(public_message)
        self.public_message = public_message
        self.status_code = status_code
        self.retry_after_seconds = retry_after_seconds


@dataclass(frozen=True)
class LLMResult:
    content: str
    model_used: str
    latency_ms: float
    token_usage: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


class GroqGateway:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def chat_completion(
        self,
        *,
        messages: list[dict[str, str]],
        model_override: str | None = None,
        temperature: float,
        max_tokens: int,
        use_fallback: bool = True,
    ) -> LLMResult:
        if not self.settings.has_groq_key:
            raise LLMGatewayError("Groq API key is not configured. Set GROQ_API_KEY in .env.")

        models = [model_override or self.settings.primary_model]
        if use_fallback and self.settings.fallback_model not in models:
            models.append(self.settings.fallback_model)

        errors: list[str] = []
        for model in models:
            try:
                return await self._attempt_with_transient_retry(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except LLMGatewayError as exc:
                errors.append(f"{model}: {exc.public_message}")
                logger.warning("Groq request failed for model %s: %s", model, exc.public_message)

        raise LLMGatewayError(
            "Groq request failed for all configured models. "
            "Check GROQ_API_KEY, model availability, and network connectivity. "
            f"Details: {' | '.join(errors)}"
        )

    async def _attempt_with_transient_retry(
        self,
        *,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> LLMResult:
        last_error: LLMGatewayError | None = None
        for attempt in range(2):
            try:
                return await self._single_request(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except LLMGatewayError as exc:
                last_error = exc
                if exc.status_code not in {408, 409, 429, 500, 502, 503, 504} or attempt == 1:
                    raise
                retry_after = exc.retry_after_seconds or (0.8 * (attempt + 1))
                await asyncio.sleep(min(max(retry_after, 0.8), 12.0))
        raise last_error or LLMGatewayError("Groq request failed.")

    async def _single_request(
        self,
        *,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> LLMResult:
        assert self.settings.groq_api_key is not None
        url = f"{self.settings.groq_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.groq_api_key.get_secret_value()}",
            "Content-Type": "application/json",
        }

        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                response = await client.post(url, json=payload, headers=headers)
        except httpx.TimeoutException as exc:
            raise LLMGatewayError("Groq request timed out.", status_code=408) from exc
        except httpx.HTTPError as exc:
            raise LLMGatewayError("Network error while calling Groq.") from exc

        latency_ms = (time.perf_counter() - start) * 1000
        if response.status_code >= 400:
            detail = self._extract_error_detail(response)
            raise LLMGatewayError(
                f"Groq returned HTTP {response.status_code}: {detail}",
                status_code=response.status_code,
                retry_after_seconds=self._extract_retry_after_seconds(response, detail),
            )

        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise LLMGatewayError("Groq returned no completion choices.")
        message = choices[0].get("message") or {}
        content = (message.get("content") or "").strip()
        if not content:
            raise LLMGatewayError("Groq returned an empty completion.")

        usage = data.get("usage") or {}
        logger.info(
            "Groq completion ok model=%s latency_ms=%.1f prompt_tokens=%s completion_tokens=%s",
            model,
            latency_ms,
            usage.get("prompt_tokens"),
            usage.get("completion_tokens"),
        )
        return LLMResult(
            content=content,
            model_used=data.get("model") or model,
            latency_ms=latency_ms,
            token_usage=usage,
            raw=data,
        )

    @staticmethod
    def _extract_error_detail(response: httpx.Response) -> str:
        try:
            data = response.json()
        except ValueError:
            return response.text[:500]
        error = data.get("error")
        if isinstance(error, dict):
            return str(error.get("message") or error.get("type") or error)
        return str(data)[:500]

    @staticmethod
    def _extract_retry_after_seconds(response: httpx.Response, detail: str) -> float | None:
        header_value = response.headers.get("retry-after")
        if header_value:
            try:
                return float(header_value)
            except ValueError:
                pass
        match = re.search(r"try again in\s+([\d.]+)\s*(ms|s|sec|secs|second|seconds)", detail, flags=re.I)
        if not match:
            return None
        value = float(match.group(1))
        unit = match.group(2).lower()
        if unit == "ms":
            return value / 1000
        return value
