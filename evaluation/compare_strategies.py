from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any


METRIC_COLUMNS = [
    "fact_recall_integration_score",
    "tone_audience_fit_score",
    "professional_email_quality_score",
    "overall_score",
]


def calculate_averages(results: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    strategies = sorted({row["strategy_name"] for row in results})
    averages: dict[str, dict[str, float]] = {}
    for strategy in strategies:
        rows = [row for row in results if row["strategy_name"] == strategy]
        averages[strategy] = {
            metric: round(mean(float(row[metric]) for row in rows), 2)
            for metric in METRIC_COLUMNS
        }
    return averages


def choose_winner(averages: dict[str, dict[str, float]]) -> str:
    return max(averages, key=lambda strategy: averages[strategy]["overall_score"])


def recommendation_for(winner: str, averages: dict[str, dict[str, float]]) -> str:
    score = averages[winner]["overall_score"]
    return (
        f"Use {winner} for production. It achieved the strongest overall average "
        f"({score:.2f}/10) and should remain paired with the quality checker and repair loop."
    )


def write_comparison_summary(
    *,
    output_path: Path,
    averages: dict[str, dict[str, float]],
    winner: str,
    results: list[dict[str, Any]],
) -> None:
    loser = min(averages, key=lambda strategy: averages[strategy]["overall_score"])
    loser_rows = [row for row in results if row["strategy_name"] == loser]
    missing_fact_count = sum(1 for row in loser_rows if row["missing_facts"])
    weaker_failure = (
        f"{loser} mainly failed on fact coverage and consistency: "
        f"{missing_fact_count} of {len(loser_rows)} samples had missing or weakly integrated facts."
    )
    if averages[loser]["tone_audience_fit_score"] < averages[loser]["professional_email_quality_score"]:
        weaker_failure = f"{loser} mainly failed on tone fit, producing less audience-specific wording."

    output_path.write_text(
        "\n".join(
            [
                "# Model/Strategy Comparison Summary",
                "",
                "## Winner",
                f"Based on the evaluation across 10 scenarios, {winner} performed better overall.",
                "",
                "## Metric Results",
                f"- Fact Recall and Integration: Strategy A = {averages['simple']['fact_recall_integration_score']:.2f}, Strategy B = {averages['advanced']['fact_recall_integration_score']:.2f}",
                f"- Tone and Audience Fit: Strategy A = {averages['simple']['tone_audience_fit_score']:.2f}, Strategy B = {averages['advanced']['tone_audience_fit_score']:.2f}",
                f"- Professional Email Quality: Strategy A = {averages['simple']['professional_email_quality_score']:.2f}, Strategy B = {averages['advanced']['professional_email_quality_score']:.2f}",
                f"- Overall Average: Strategy A = {averages['simple']['overall_score']:.2f}, Strategy B = {averages['advanced']['overall_score']:.2f}",
                "",
                "## Biggest Failure Mode",
                weaker_failure,
                "",
                "## Production Recommendation",
                recommendation_for(winner, averages),
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_final_report(
    *,
    output_path: Path,
    comparison_path: Path,
    json_path: Path,
    csv_path: Path,
    averages: dict[str, dict[str, float]],
    winner: str,
) -> None:
    prompt_template = (Path(__file__).resolve().parents[1] / "docs" / "prompt_template.md").read_text(encoding="utf-8")
    metric_definitions = (Path(__file__).resolve().parents[1] / "docs" / "metric_definitions.md").read_text(encoding="utf-8")
    comparison = comparison_path.read_text(encoding="utf-8")
    output_path.write_text(
        "\n".join(
            [
                "# Final Report: Email Generation Assistant",
                "",
                "## Project Summary",
                "This project builds a production-ready prototype that generates polished professional English emails from Intent, Key Facts, and Tone using Groq-hosted LLMs through a FastAPI backend.",
                "",
                "## Recommended Strategy",
                f"The recommended production strategy is `{winner}` with an overall average of {averages[winner]['overall_score']:.2f}/10.",
                "",
                "## Advanced Prompting Technique",
                "Strategy B uses Role-Playing + Few-Shot Examples + Structured JSON Output + Self-Check/Repair Prompting. This improves quality because the model receives a precise professional role, concrete examples, a parseable output contract, and a repair pass when fact coverage or quality thresholds are not met.",
                "",
                "## Exact Strategy B Prompt Template",
                prompt_template,
                "",
                "## Custom Metrics",
                metric_definitions,
                "",
                "## Raw Evaluation Data",
                f"- CSV: `{csv_path.as_posix()}`",
                f"- JSON: `{json_path.as_posix()}`",
                "",
                "## Comparative Analysis",
                comparison,
                "",
                "## PDF Export",
                "PDF generation is not automated in this repository. Export this Markdown file to PDF with one of these commands:",
                "",
                "```bash",
                "pandoc reports/final_report.md -o reports/final_report.pdf",
                "# or use VS Code Markdown Preview: Open Preview -> Print -> Save as PDF",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )


def load_results_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    json_path = root / "reports" / "evaluation_results.json"
    data = load_results_json(json_path)
    averages = calculate_averages(data["strategy_results"])
    winner = choose_winner(averages)
    summary_path = root / "reports" / "comparison_summary.md"
    write_comparison_summary(output_path=summary_path, averages=averages, winner=winner, results=data["strategy_results"])
    write_final_report(
        output_path=root / "reports" / "final_report.md",
        comparison_path=summary_path,
        json_path=json_path,
        csv_path=root / "reports" / "evaluation_results.csv",
        averages=averages,
        winner=winner,
    )


if __name__ == "__main__":
    main()

