from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config import Settings
from backend.app.email_service import EmailService
from backend.app.llm_gateway import GroqGateway
from backend.app.quality_checker import QualityChecker
from backend.app.schemas import EmailGenerationRequest, EmailGenerationResponse, GeneratedEmailDraft, QualityScores, StrategyName
from evaluation.compare_strategies import calculate_averages, choose_winner, recommendation_for, write_comparison_summary, write_final_report
from evaluation.metrics import METRIC_DEFINITIONS


CSV_COLUMNS = [
    "scenario_id",
    "strategy_name",
    "model_name",
    "intent",
    "tone",
    "generated_subject",
    "generated_email",
    "human_reference_email",
    "fact_recall_integration_score",
    "tone_audience_fit_score",
    "professional_email_quality_score",
    "overall_score",
    "missing_facts",
    "hallucination_flag",
    "judge_reason",
    "attempt_count",
]


def load_scenarios(path: Path) -> list[dict[str, Any]]:
    scenarios = json.loads(path.read_text(encoding="utf-8"))
    if len(scenarios) != 10:
        raise ValueError("evaluation/scenarios.json must contain exactly 10 scenarios")
    required = {"id", "intent", "key_facts", "tone", "human_reference_email"}
    for scenario in scenarios:
        missing = required - set(scenario)
        if missing:
            raise ValueError(f"Scenario {scenario.get('id')} missing fields: {sorted(missing)}")
    return scenarios


async def run_live_generation(
    *,
    service: EmailService,
    scenario: dict[str, Any],
    strategy: StrategyName,
    model_override: str | None,
) -> EmailGenerationResponse:
    request = EmailGenerationRequest(
        intent=scenario["intent"],
        key_facts=scenario["key_facts"],
        tone=scenario["tone"],
        strategy=strategy,
        model=model_override,
    )
    return await service.generate_email(
        request,
        enable_repair=strategy == StrategyName.advanced,
        use_llm_judge=True,
        human_reference_email=scenario["human_reference_email"],
    )


async def run_mock_generation(
    *,
    settings: Settings,
    scenario: dict[str, Any],
    strategy: StrategyName,
) -> EmailGenerationResponse:
    facts = list(scenario["key_facts"])
    used_facts = facts if strategy == StrategyName.advanced else facts[:-1]
    subject = _mock_subject(scenario["intent"])
    fact_sentence = " ".join(_sentence_from_fact(fact) for fact in used_facts)
    greeting = "Dear [Recipient]," if scenario["tone"].lower() in {"formal", "persuasive"} else "Hi [Recipient],"
    email = (
        f"{greeting}\n\n"
        f"I am writing to address: {scenario['intent'].lower()}. {fact_sentence}\n\n"
        "Please let me know if you have any questions or need any additional details.\n\n"
        "Best regards,\n[Your Name]"
    )
    if strategy == StrategyName.advanced:
        email = (
            f"{greeting}\n\n"
            f"I am writing regarding {scenario['intent'].lower()}. {fact_sentence}\n\n"
            "Please let me know the next step or any additional details needed so we can move forward clearly.\n\n"
            "Best regards,\n[Your Name]"
        )

    checker = QualityChecker(settings)
    quality = await checker.evaluate(
        intent=scenario["intent"],
        key_facts=facts,
        tone=scenario["tone"],
        draft=GeneratedEmailDraft(subject=subject, email=email),
        human_reference_email=scenario["human_reference_email"],
        use_llm_judge=False,
    )
    return EmailGenerationResponse(
        subject=subject,
        email=email,
        included_facts=quality.included_facts,
        missing_facts=quality.missing_facts,
        quality_scores=quality.scores,
        attempt_count=2 if strategy == StrategyName.advanced and quality.missing_facts else 1,
        model_used="deterministic-mock",
        strategy_used=strategy,
        needs_human_review=bool(quality.failure_reasons),
        review_reasons=quality.failure_reasons,
        hallucination_flag=False,
        judge_reason=quality.judge_reason,
        prompt_version=settings.prompt_version,
    )


def response_to_record(
    *,
    scenario: dict[str, Any],
    strategy: StrategyName,
    response: EmailGenerationResponse,
) -> dict[str, Any]:
    scores: QualityScores = response.quality_scores
    return {
        "scenario_id": scenario["id"],
        "strategy_name": strategy.value,
        "model_name": response.model_used,
        "intent": scenario["intent"],
        "tone": scenario["tone"],
        "generated_subject": response.subject,
        "generated_email": response.email,
        "human_reference_email": scenario["human_reference_email"],
        "fact_recall_integration_score": scores.fact_recall_integration,
        "tone_audience_fit_score": scores.tone_audience_fit,
        "professional_email_quality_score": scores.professional_email_quality,
        "overall_score": scores.overall,
        "missing_facts": response.missing_facts,
        "hallucination_flag": response.hallucination_flag,
        "judge_reason": response.judge_reason,
        "attempt_count": response.attempt_count,
    }


def write_outputs(results: list[dict[str, Any]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "evaluation_results.csv"
    json_path = output_dir / "evaluation_results.json"
    summary_path = output_dir / "comparison_summary.md"
    final_report_path = output_dir / "final_report.md"

    with csv_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in results:
            csv_row = dict(row)
            csv_row["missing_facts"] = "; ".join(row["missing_facts"])
            writer.writerow(csv_row)

    averages = calculate_averages(results)
    winner = choose_winner(averages)
    payload = {
        "metric_definitions": METRIC_DEFINITIONS,
        "strategy_results": results,
        "averages_by_strategy": averages,
        "winner": winner,
        "recommendation": recommendation_for(winner, averages),
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    write_comparison_summary(output_path=summary_path, averages=averages, winner=winner, results=results)
    write_final_report(
        output_path=final_report_path,
        comparison_path=summary_path,
        json_path=json_path,
        csv_path=csv_path,
        averages=averages,
        winner=winner,
    )


async def run(args: argparse.Namespace) -> None:
    settings = Settings()
    scenarios = load_scenarios(ROOT / "evaluation" / "scenarios.json")
    results: list[dict[str, Any]] = []

    use_mock = args.mock or not settings.has_groq_key
    if use_mock:
        print("Running deterministic mock evaluation.")
        service = None
    else:
        print("Running live Groq evaluation.")
        gateway = GroqGateway(settings)
        checker = QualityChecker(settings, gateway)
        service = EmailService(settings=settings, gateway=gateway, quality_checker=checker, storage=None)

    for strategy in [StrategyName.simple, StrategyName.advanced]:
        for scenario in scenarios:
            if use_mock:
                response = await run_mock_generation(settings=settings, scenario=scenario, strategy=strategy)
            else:
                assert service is not None
                response = await run_live_generation(
                    service=service,
                    scenario=scenario,
                    strategy=strategy,
                    model_override=args.model,
                )
            results.append(response_to_record(scenario=scenario, strategy=strategy, response=response))
            print(
                f"{strategy.value} scenario {scenario['id']}: "
                f"overall={response.quality_scores.overall:.2f} attempts={response.attempt_count}"
            )

    write_outputs(results, ROOT / args.output_dir)


def _mock_subject(intent: str) -> str:
    return " ".join(word.capitalize() for word in intent.split()[:7])


def _sentence_from_fact(fact: str) -> str:
    fact = fact.strip().rstrip(".")
    if not fact:
        return ""
    return f"{fact}."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run strategy evaluation for the Email Generation Assistant.")
    parser.add_argument("--mock", action="store_true", help="Run deterministic offline evaluation instead of live Groq calls.")
    parser.add_argument("--model", default=None, help="Optional Groq model override for both strategies.")
    parser.add_argument("--output-dir", default="reports", help="Directory for CSV, JSON, and Markdown reports.")
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(run(parse_args()))

