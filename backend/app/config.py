from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[str(PROJECT_ROOT / ".env"), str(PROJECT_ROOT / "backend" / ".env")],
        env_file_encoding="utf-8-sig",
        extra="ignore",
    )

    groq_api_key: SecretStr | None = Field(default=None, alias="GROQ_API_KEY")
    primary_model: str = Field(default="openai/gpt-oss-120b", alias="PRIMARY_MODEL")
    fallback_model: str = Field(default="llama-3.3-70b-versatile", alias="FALLBACK_MODEL")
    judge_model: str = Field(default="llama-3.1-8b-instant", alias="JUDGE_MODEL")
    groq_base_url: str = Field(default="https://api.groq.com/openai/v1", alias="GROQ_BASE_URL")
    prompt_version: str = Field(default="email-production-v1.0.0", alias="PROMPT_VERSION")

    request_timeout_seconds: float = Field(default=35.0, alias="REQUEST_TIMEOUT_SECONDS")
    max_generation_tokens: int = Field(default=1100, alias="MAX_GENERATION_TOKENS")
    max_judge_tokens: int = Field(default=800, alias="MAX_JUDGE_TOKENS")
    max_body_bytes: int = Field(default=16_384, alias="MAX_BODY_BYTES")

    generation_temperature: float = 0.4
    repair_temperature: float = 0.25
    judge_temperature: float = 0.0

    fact_threshold: float = 7.5
    tone_threshold: float = 8.0
    quality_threshold: float = 8.0
    overall_threshold: float = 8.2
    max_attempts: int = 3

    sqlite_path: Path = PROJECT_ROOT / "data" / "email_generations.db"

    @property
    def has_groq_key(self) -> bool:
        return bool(self.groq_api_key and self.groq_api_key.get_secret_value().strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
