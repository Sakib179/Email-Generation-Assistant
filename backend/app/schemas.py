from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrategyName(str, Enum):
    simple = "simple"
    advanced = "advanced"


class EmailGenerationRequest(BaseModel):
    intent: str = Field(..., min_length=1, max_length=1000)
    key_facts: list[str] = Field(..., min_length=1, max_length=15)
    tone: str = Field(..., min_length=1, max_length=80)
    strategy: StrategyName = StrategyName.advanced
    model: str | None = Field(default=None, max_length=120)

    @field_validator("intent", "tone", mode="before")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("key_facts", mode="before")
    @classmethod
    def normalize_facts(cls, value: Any) -> list[str]:
        if not isinstance(value, list):
            raise ValueError("key_facts must be a list of facts")
        facts = [str(item).strip() for item in value if str(item).strip()]
        if not facts:
            raise ValueError("At least one key fact is required")
        return facts

    @field_validator("model", mode="before")
    @classmethod
    def blank_model_to_none(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class EmailEvaluationRequest(BaseModel):
    intent: str = Field(..., min_length=1, max_length=1000)
    key_facts: list[str] = Field(..., min_length=1, max_length=15)
    tone: str = Field(..., min_length=1, max_length=80)
    generated_email: str = Field(..., min_length=1, max_length=8000)
    generated_subject: str | None = Field(default=None, max_length=250)
    human_reference_email: str | None = Field(default=None, max_length=8000)

    @field_validator("intent", "tone", "generated_email", mode="before")
    @classmethod
    def strip_text(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("key_facts", mode="before")
    @classmethod
    def normalize_facts(cls, value: Any) -> list[str]:
        if not isinstance(value, list):
            raise ValueError("key_facts must be a list of facts")
        facts = [str(item).strip() for item in value if str(item).strip()]
        if not facts:
            raise ValueError("At least one key fact is required")
        return facts


class QualityScores(BaseModel):
    fact_recall_integration: float = Field(..., ge=0, le=10)
    tone_audience_fit: float = Field(..., ge=0, le=10)
    professional_email_quality: float = Field(..., ge=0, le=10)
    overall: float = Field(..., ge=0, le=10)


class GeneratedEmailDraft(BaseModel):
    subject: str = Field(..., min_length=1, max_length=250)
    email: str = Field(..., min_length=1, max_length=8000)
    included_facts: list[str] = Field(default_factory=list)
    missing_facts: list[str] = Field(default_factory=list)
    tone_used: str | None = None
    notes: str | None = None

    @field_validator("subject", "email", mode="before")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class JudgeScores(BaseModel):
    fact_recall_integration_score: float = Field(..., ge=0, le=10)
    tone_audience_fit_score: float = Field(..., ge=0, le=10)
    professional_email_quality_score: float = Field(..., ge=0, le=10)
    overall_score: float = Field(..., ge=0, le=10)
    missing_facts: list[str] = Field(default_factory=list)
    hallucination_flag: bool = False
    reason: str = ""


class EmailGenerationResponse(BaseModel):
    subject: str
    email: str
    included_facts: list[str]
    missing_facts: list[str]
    quality_scores: QualityScores
    attempt_count: int
    model_used: str
    strategy_used: StrategyName
    needs_human_review: bool = False
    review_reasons: list[str] = Field(default_factory=list)
    hallucination_flag: bool = False
    judge_reason: str = ""
    prompt_version: str


class EmailEvaluationResponse(BaseModel):
    quality_scores: QualityScores
    missing_facts: list[str]
    hallucination_flag: bool = False
    judge_reason: str = ""


class HealthResponse(BaseModel):
    status: str
    groq_api_key_configured: bool
    primary_model: str
    fallback_model: str
    judge_model: str
    prompt_version: str
    storage: str


class HistoryItem(BaseModel):
    id: int
    created_at: str
    intent: str
    tone: str
    strategy: str
    model_used: str
    subject: str
    email: str
    quality_scores: QualityScores
    needs_human_review: bool


class HistoryResponse(BaseModel):
    items: list[HistoryItem]


class GenerationLogRecord(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    intent: str
    key_facts: list[str]
    tone: str
    strategy: str
    model_used: str
    subject: str
    email: str
    quality_scores: QualityScores
    attempt_count: int
    needs_human_review: bool
    prompt_version: str
    token_usage: dict[str, Any] = Field(default_factory=dict)
    latency_ms: float | None = None
