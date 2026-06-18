from __future__ import annotations

from .config import Settings
from .llm_gateway import GroqGateway, LLMResult
from .prompt_templates import build_repair_messages


class RepairService:
    def __init__(self, settings: Settings, gateway: GroqGateway):
        self.settings = settings
        self.gateway = gateway

    async def repair(
        self,
        *,
        intent: str,
        key_facts: list[str],
        tone: str,
        subject: str,
        generated_email: str,
        failure_reasons: list[str],
        model_override: str | None,
    ) -> LLMResult:
        prompt = build_repair_messages(
            intent=intent,
            key_facts=key_facts,
            tone=tone,
            subject=subject,
            generated_email=generated_email,
            failure_reasons=failure_reasons,
            prompt_version=self.settings.prompt_version,
        )
        return await self.gateway.chat_completion(
            messages=prompt.messages,
            model_override=model_override,
            temperature=self.settings.repair_temperature,
            max_tokens=self.settings.max_generation_tokens,
            use_fallback=True,
        )

