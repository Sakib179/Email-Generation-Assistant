from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from .config import Settings
from .llm_gateway import GroqGateway, LLMGatewayError, LLMResult
from .prompt_templates import build_generation_messages
from .quality_checker import QualityChecker
from .repair_service import RepairService
from .schemas import (
    EmailGenerationRequest,
    EmailGenerationResponse,
    GeneratedEmailDraft,
    GenerationLogRecord,
    QualityScores,
    StrategyName,
)
from .storage import Storage


logger = logging.getLogger(__name__)


@dataclass
class AttemptResult:
    draft: GeneratedEmailDraft
    quality_scores: QualityScores
    missing_facts: list[str]
    included_facts: list[str]
    failure_reasons: list[str]
    model_used: str
    token_usage: dict[str, Any] = field(default_factory=dict)
    latency_ms: float | None = None
    hallucination_flag: bool = False
    judge_reason: str = ""

    @property
    def is_passing(self) -> bool:
        return not self.failure_reasons


class EmailService:
    def __init__(
        self,
        *,
        settings: Settings,
        gateway: GroqGateway,
        quality_checker: QualityChecker,
        storage: Storage | None = None,
    ):
        self.settings = settings
        self.gateway = gateway
        self.quality_checker = quality_checker
        self.repair_service = RepairService(settings, gateway)
        self.storage = storage

    async def generate_email(
        self,
        request: EmailGenerationRequest,
        *,
        enable_repair: bool | None = None,
        use_llm_judge: bool = True,
        human_reference_email: str | None = None,
    ) -> EmailGenerationResponse:
        repair_enabled = enable_repair if enable_repair is not None else request.strategy == StrategyName.advanced
        attempts: list[AttemptResult] = []

        initial = build_generation_messages(
            intent=request.intent,
            key_facts=request.key_facts,
            tone=request.tone,
            strategy=request.strategy,
            prompt_version=self.settings.prompt_version,
        )
        try:
            llm_result = await self.gateway.chat_completion(
                messages=initial.messages,
                model_override=request.model,
                temperature=self.settings.generation_temperature,
                max_tokens=self.settings.max_generation_tokens,
                use_fallback=True,
            )
        except LLMGatewayError:
            raise

        attempt = await self._build_attempt(
            request=request,
            llm_result=llm_result,
            use_llm_judge=use_llm_judge,
            human_reference_email=human_reference_email,
        )
        attempts.append(attempt)

        while repair_enabled and attempts[-1].failure_reasons and len(attempts) < self.settings.max_attempts:
            previous = attempts[-1]
            repair_result = await self.repair_service.repair(
                intent=request.intent,
                key_facts=request.key_facts,
                tone=request.tone,
                subject=previous.draft.subject,
                generated_email=previous.draft.email,
                failure_reasons=previous.failure_reasons,
                model_override=request.model,
            )
            attempts.append(
                await self._build_attempt(
                    request=request,
                    llm_result=repair_result,
                    use_llm_judge=use_llm_judge,
                    human_reference_email=human_reference_email,
                )
            )

        best = max(attempts, key=lambda item: item.quality_scores.overall)
        needs_human_review = bool(best.failure_reasons)
        response = EmailGenerationResponse(
            intent=request.intent,
            key_facts=request.key_facts,
            subject=best.draft.subject,
            email=best.draft.email,
            included_facts=best.included_facts or best.draft.included_facts,
            missing_facts=best.missing_facts,
            quality_scores=best.quality_scores,
            attempt_count=len(attempts),
            model_used=best.model_used,
            strategy_used=request.strategy,
            needs_human_review=needs_human_review,
            review_reasons=best.failure_reasons if needs_human_review else [],
            hallucination_flag=best.hallucination_flag,
            judge_reason=best.judge_reason,
            prompt_version=self.settings.prompt_version,
        )

        logger.info(
            "generation complete prompt_version=%s strategy=%s model=%s attempts=%s overall=%.2f review=%s",
            self.settings.prompt_version,
            request.strategy.value,
            response.model_used,
            response.attempt_count,
            response.quality_scores.overall,
            response.needs_human_review,
        )
        if self.storage:
            self.storage.save_generation(
                GenerationLogRecord(
                    intent=request.intent,
                    key_facts=request.key_facts,
                    tone=request.tone,
                    strategy=request.strategy.value,
                    model_used=response.model_used,
                    subject=response.subject,
                    email=response.email,
                    quality_scores=response.quality_scores,
                    included_facts=response.included_facts,
                    missing_facts=response.missing_facts,
                    attempt_count=response.attempt_count,
                    needs_human_review=response.needs_human_review,
                    review_reasons=response.review_reasons,
                    hallucination_flag=response.hallucination_flag,
                    judge_reason=response.judge_reason,
                    prompt_version=response.prompt_version,
                    token_usage=best.token_usage,
                    latency_ms=best.latency_ms,
                )
            )
        return response

    async def _build_attempt(
        self,
        *,
        request: EmailGenerationRequest,
        llm_result: LLMResult,
        use_llm_judge: bool,
        human_reference_email: str | None,
    ) -> AttemptResult:
        draft = parse_generation_output(llm_result.content, request)
        quality = await self.quality_checker.evaluate(
            intent=request.intent,
            key_facts=request.key_facts,
            tone=request.tone,
            draft=draft,
            human_reference_email=human_reference_email,
            use_llm_judge=use_llm_judge,
        )
        return AttemptResult(
            draft=draft,
            quality_scores=quality.scores,
            missing_facts=quality.missing_facts,
            included_facts=quality.included_facts,
            failure_reasons=quality.failure_reasons,
            model_used=llm_result.model_used,
            token_usage=llm_result.token_usage,
            latency_ms=llm_result.latency_ms,
            hallucination_flag=quality.hallucination_flag,
            judge_reason=quality.judge_reason,
        )


def parse_generation_output(content: str, request: EmailGenerationRequest) -> GeneratedEmailDraft:
    try:
        data = _loads_json_object(content)
        return GeneratedEmailDraft.model_validate(data)
    except Exception:
        return _parse_plain_text_generation(content, request)


def _loads_json_object(content: str) -> dict[str, Any]:
    content = content.strip()
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    start = content.find("{")
    end = content.rfind("}")
    if start >= 0 and end > start:
        data = json.loads(content[start : end + 1])
        if isinstance(data, dict):
            return data
    raise ValueError("No valid JSON object found")


def _parse_plain_text_generation(content: str, request: EmailGenerationRequest) -> GeneratedEmailDraft:
    lines = [line.rstrip() for line in content.strip().splitlines() if line.strip()]
    subject = ""
    body_lines = []
    for line in lines:
        match = re.match(r"^\s*(subject(?: line)?):\s*(.+)$", line, flags=re.I)
        if match and not subject:
            subject = match.group(2).strip().strip('"')
        else:
            body_lines.append(line)
    if not subject:
        subject = _subject_from_intent(request.intent)
    body = "\n".join(body_lines).strip() or content.strip()
    return GeneratedEmailDraft(
        subject=subject,
        email=body,
        included_facts=[],
        missing_facts=[],
        tone_used=request.tone,
        notes="Parsed from plain-text model output.",
    )


def _subject_from_intent(intent: str) -> str:
    words = re.findall(r"[A-Za-z0-9$#-]+", intent)
    short = " ".join(words[:8]).strip()
    return short.title() if short else "Professional Email"
