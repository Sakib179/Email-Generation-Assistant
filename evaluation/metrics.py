from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import Settings
from backend.app.quality_checker import QualityChecker, QualityResult
from backend.app.schemas import GeneratedEmailDraft


METRIC_DEFINITIONS: dict[str, dict[str, str]] = {
    "fact_recall_integration_score": {
        "scale": "0-10",
        "definition": "Checks whether every required key fact appears correctly and naturally in the email.",
        "logic": "70% deterministic fact presence and 30% LLM natural-integration judgment when the judge is available.",
    },
    "tone_audience_fit_score": {
        "scale": "0-10",
        "definition": "Rates whether the generated email matches the requested tone while staying professional.",
        "logic": "LLM-as-a-judge score with deterministic tone fallback.",
    },
    "professional_email_quality_score": {
        "scale": "0-10",
        "definition": "Rates subject, greeting, body clarity, CTA, closing, conciseness, grammar, and fluency.",
        "logic": "40% deterministic structure checks and 60% LLM quality judgment when the judge is available.",
    },
}


async def score_email(
    *,
    settings: Settings,
    scenario: dict[str, Any],
    subject: str,
    email: str,
    gateway=None,
    use_llm_judge: bool = True,
) -> QualityResult:
    checker = QualityChecker(settings, gateway)
    draft = GeneratedEmailDraft(subject=subject, email=email)
    return await checker.evaluate(
        intent=scenario["intent"],
        key_facts=scenario["key_facts"],
        tone=scenario["tone"],
        draft=draft,
        human_reference_email=scenario.get("human_reference_email"),
        use_llm_judge=use_llm_judge,
    )

