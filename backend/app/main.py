from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .email_service import EmailService
from .llm_gateway import GroqGateway, LLMGatewayError
from .quality_checker import QualityChecker
from .schemas import (
    EmailEvaluationRequest,
    EmailEvaluationResponse,
    EmailGenerationRequest,
    EmailGenerationResponse,
    HealthResponse,
    HistoryResponse,
)
from .storage import Storage


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

settings = get_settings()
storage = Storage(settings.sqlite_path)
gateway = GroqGateway(settings)
quality_checker = QualityChecker(settings, gateway)
email_service = EmailService(settings=settings, gateway=gateway, quality_checker=quality_checker, storage=storage)

app = FastAPI(
    title="Email Generation Assistant API",
    version="1.0.0",
    description="Groq-backed professional English email generation API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_size_limit(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > settings.max_body_bytes:
        return JSONResponse(status_code=413, content={"detail": "Request body is too large."})
    return await call_next(request)


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        groq_api_key_configured=settings.has_groq_key,
        primary_model=settings.primary_model,
        fallback_model=settings.fallback_model,
        judge_model=settings.judge_model,
        prompt_version=settings.prompt_version,
        storage=str(settings.sqlite_path),
    )


@app.post("/api/generate-email", response_model=EmailGenerationResponse)
async def generate_email(request: EmailGenerationRequest) -> EmailGenerationResponse:
    try:
        return await email_service.generate_email(request)
    except LLMGatewayError as exc:
        raise HTTPException(status_code=502, detail=exc.public_message) from exc


@app.post("/api/evaluate-email", response_model=EmailEvaluationResponse)
async def evaluate_email(request: EmailEvaluationRequest) -> EmailEvaluationResponse:
    from .schemas import GeneratedEmailDraft

    draft = GeneratedEmailDraft(
        subject=request.generated_subject or "Generated Email",
        email=request.generated_email,
        included_facts=[],
        missing_facts=[],
        tone_used=request.tone,
    )
    quality = await quality_checker.evaluate(
        intent=request.intent,
        key_facts=request.key_facts,
        tone=request.tone,
        draft=draft,
        human_reference_email=request.human_reference_email,
        use_llm_judge=True,
    )
    return EmailEvaluationResponse(
        quality_scores=quality.scores,
        missing_facts=quality.missing_facts,
        hallucination_flag=quality.hallucination_flag,
        judge_reason=quality.judge_reason,
    )


@app.get("/api/history", response_model=HistoryResponse)
async def history() -> HistoryResponse:
    return HistoryResponse(items=storage.list_history(limit=20))


@app.delete("/api/history/{item_id}", status_code=204)
async def delete_history_item(item_id: int) -> Response:
    if not storage.delete_history_item(item_id):
        raise HTTPException(status_code=404, detail="History item not found.")
    return Response(status_code=204)
