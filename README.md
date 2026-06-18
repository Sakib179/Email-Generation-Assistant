# Email Generation Assistant

Production-ready prototype for generating polished professional English emails from three required inputs: Intent, Key Facts, and Tone. The app uses Groq-hosted LLMs through a FastAPI backend, keeps API keys server-side, evaluates output quality with three custom metrics, and compares a simple baseline prompt against an advanced production prompt.

## Features

- English-only email generation with subject, greeting, body, call-to-action, and sign-off.
- Required inputs: Intent, Key Facts, Tone.
- Groq provider integration with configurable primary, fallback, and judge models.
- Strategy comparison: simple baseline prompt vs. advanced production prompt.
- Advanced prompt engineering: Role-Playing + Few-Shot Examples + Structured JSON Output + Self-Check/Repair Prompting.
- Quality checker with fact recall, tone fit, and professional email quality metrics.
- Auto-repair loop for missing facts or low scores, capped at three attempts.
- SQLite generation history for the local prototype.
- Evaluation suite with 10 fixed scenarios, human reference emails, CSV/JSON raw data, comparison summary, and final report.

## Tech Stack

- Frontend: Next.js, TypeScript, Tailwind CSS, lucide-react.
- Backend: FastAPI, Pydantic, HTTPX, SQLite.
- Evaluation and tests: pytest plus Python evaluation scripts.
- LLM provider: Groq OpenAI-compatible Chat Completions API.

## Architecture

User input flows from the Next.js UI to `POST /api/generate-email`. FastAPI validates the request, builds either the baseline or advanced prompt, calls Groq server-side, parses JSON or extracts a fallback email, evaluates the output, repairs weak generations when enabled, persists the final response to SQLite, and returns structured scores to the UI.

```text
Next.js UI -> FastAPI API -> Prompt Builder -> Groq Gateway
                          -> Output Parser -> Quality Checker/Judge
                          -> Repair Loop -> SQLite History -> UI
```

## Environment Variables

Copy `.env.example` to `.env` in the project root and set:

- `GROQ_API_KEY`: Groq API key. Never expose this in frontend code.
- `PRIMARY_MODEL`: default `openai/gpt-oss-120b`.
- `FALLBACK_MODEL`: default `llama-3.3-70b-versatile`.
- `JUDGE_MODEL`: default `llama-3.1-8b-instant`.
- `GROQ_BASE_URL`: default `https://api.groq.com/openai/v1`.
- `NEXT_PUBLIC_API_BASE_URL`: frontend API base URL, default `http://localhost:8000`.

The model IDs above were verified against Groq docs on June 18, 2026. Keep them configurable because model access can vary by account and over time.

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
cd frontend
npm install
```

## Run Backend

From the project root:

```bash
.venv\Scripts\activate
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/api/health
```

## Run Frontend

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000`.

## Run Tests

```bash
.venv\Scripts\activate
pytest backend/tests
cd frontend
npm run type-check
```

Live LLM integration is optional and only runs when both variables are set:

```bash
set GROQ_API_KEY=your-key
set RUN_LIVE_LLM_TESTS=true
pytest backend/tests/test_live_groq.py
```

## Run Evaluation

Run live evaluation when `GROQ_API_KEY` is configured:

```bash
.venv\Scripts\activate
python evaluation/run_evaluation.py
```

Run deterministic offline evaluation:

```bash
python evaluation/run_evaluation.py --mock
```

Outputs are saved under `reports/`:

- `evaluation_results.csv`
- `evaluation_results.json`
- `comparison_summary.md`
- `final_report.md`

## Compare Strategies or Models

By default, `evaluation/run_evaluation.py` runs the same 10 scenarios through:

- Strategy A: simple baseline prompt.
- Strategy B: advanced production prompt with repair enabled.

The same primary Groq model is used for both strategies unless you pass `--model model-id`. This isolates the impact of prompt engineering. Optional model comparison can be performed by rerunning with a different `--model` value and comparing report outputs.

## Prompt Engineering Technique

The production strategy combines:

- Role-Playing: the model acts as a senior executive communication specialist.
- Few-Shot Examples: two complete business email examples demonstrate desired structure and tone.
- Structured JSON Output: responses must match a fixed JSON schema for reliable parsing.
- Self-Check/Repair Prompting: the model silently checks facts, tone, professionalism, and unsupported claims; weak outputs are repaired with explicit failure reasons.

The exact production prompt is stored in `docs/prompt_template.md` and embedded in `reports/final_report.md`.

## Custom Metrics

The system implements exactly three custom metrics:

- Fact Recall and Integration Score: checks whether every required fact is present accurately and naturally.
- Tone and Audience Fit Score: checks requested tone, professionalism, and audience fit.
- Professional Email Quality Score: checks subject, greeting, body clarity, CTA, closing, conciseness, grammar, and fluency.

Definitions and scoring logic are in `docs/metric_definitions.md`.

## Production Notes

- API keys stay server-side only.
- `.env` is ignored by Git; `.env.example` contains placeholders only.
- Request sizes and field lengths are capped.
- Groq calls include timeout handling, transient retries, and fallback model support.
- The service logs prompt version, model, strategy, attempts, latency, token usage, scores, and review status.
- For public deployment, add user authentication and distributed rate limiting at the API gateway or reverse proxy layer.
- SQLite is used for local history; PostgreSQL is included in Docker Compose as the production-like upgrade path.

## Known Limitations and Future Improvements

- LLM-as-a-judge scoring is useful but not a substitute for human review in high-stakes communication.
- Local rate limiting is documented but not enabled as a distributed service.
- Frontend tests are limited to TypeScript checks; Playwright can be added for browser E2E coverage.
- PDF export is documented in the final report; Markdown output is generated automatically.
- `npm audit --omit=dev` currently reports a moderate advisory in Next.js's bundled `postcss@8.4.31`. The direct `postcss` dependency is patched, Next.js `16.2.9` is the latest version available in this environment, and npm's forced fix suggests an invalid downgrade. Monitor the next Next.js patch release before public deployment.
