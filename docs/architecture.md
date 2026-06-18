# Architecture

## Runtime Flow

```text
Browser
  -> Next.js EmailForm
  -> POST /api/generate-email
  -> FastAPI request validation
  -> Prompt builder
  -> Groq gateway
  -> JSON parser/plain-text fallback
  -> Quality checker
  -> Optional repair loop
  -> SQLite history
  -> GeneratedEmailCard
```

## Backend Modules

- `config.py`: environment variable loading and production thresholds.
- `schemas.py`: Pydantic request and response contracts.
- `prompt_templates.py`: baseline, advanced, few-shot, and repair prompts.
- `llm_gateway.py`: Groq API calls with timeout, transient retry, fallback model, and friendly errors.
- `quality_checker.py`: deterministic checks plus optional LLM-as-a-judge scoring.
- `repair_service.py`: repair prompt orchestration.
- `email_service.py`: end-to-end generation, parsing, scoring, repair, and response construction.
- `storage.py`: SQLite history for the local prototype.
- `main.py`: FastAPI routes and middleware.

## Frontend Modules

- `EmailForm.tsx`: required input form and optional strategy/model controls.
- `GeneratedEmailCard.tsx`: subject, body, quality badges, fact coverage, copy, and regenerate actions.
- `HistoryPanel.tsx`: recent saved generations.
- `api.ts`: typed API client.

## Data and Reports

- `evaluation/scenarios.json`: fixed 10-scenario dataset with human reference emails.
- `evaluation/run_evaluation.py`: runs both strategies and writes raw outputs.
- `evaluation/compare_strategies.py`: computes averages and writes Markdown reports.
- `reports/`: CSV, JSON, comparison summary, and final report.

## Production Path

The local prototype uses SQLite for simplicity. PostgreSQL can replace it behind the same storage boundary; `docker-compose.yml` already includes a local PostgreSQL service. Public deployment should add authentication, distributed rate limiting, structured log shipping, and persistent background evaluation jobs.

