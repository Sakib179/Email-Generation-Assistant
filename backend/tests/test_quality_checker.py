import pytest

from backend.app.config import Settings
from backend.app.quality_checker import QualityChecker, _normalize_judge_payload
from backend.app.schemas import GeneratedEmailDraft


@pytest.mark.asyncio
async def test_quality_checker_scores_good_email_higher_than_bad_email():
    settings = Settings()
    checker = QualityChecker(settings)
    facts = [
        "Meeting was yesterday",
        "Discussed website redesign",
        "Client asked for timeline",
        "Proposal due Friday",
    ]
    good = GeneratedEmailDraft(
        subject="Follow-Up on Website Redesign Timeline",
        email=(
            "Dear [Recipient],\n\n"
            "Thank you for meeting yesterday to discuss the website redesign. "
            "I understand you asked for a timeline, and I will include it in the proposal due Friday.\n\n"
            "Please let me know if there is anything else you would like included.\n\n"
            "Best regards,\n[Your Name]"
        ),
    )
    bad = GeneratedEmailDraft(
        subject="Follow-Up",
        email="Hello,\n\nThanks for the chat. I will send something soon.\n\nRegards,\n[Your Name]",
    )

    good_result = await checker.evaluate(
        intent="Follow up after a client meeting",
        key_facts=facts,
        tone="Formal",
        draft=good,
        use_llm_judge=False,
    )
    bad_result = await checker.evaluate(
        intent="Follow up after a client meeting",
        key_facts=facts,
        tone="Formal",
        draft=bad,
        use_llm_judge=False,
    )

    assert good_result.scores.fact_recall_integration > bad_result.scores.fact_recall_integration
    assert good_result.scores.overall > bad_result.scores.overall
    assert "Proposal due Friday" not in good_result.missing_facts
    assert "Proposal due Friday" in bad_result.missing_facts


def test_normalize_judge_payload_clamps_invalid_scores():
    payload = _normalize_judge_payload(
        {
            "fact_recall_integration_score": 9,
            "tone_audience_fit_score": "8.5",
            "professional_email_quality_score": 11,
            "overall_score": 23,
            "missing_facts": "not-a-list",
            "hallucination_flag": 0,
        }
    )

    assert payload["professional_email_quality_score"] == 10
    assert payload["overall_score"] == 10
    assert payload["missing_facts"] == []


def test_fact_matching_accepts_natural_business_paraphrases():
    checker = QualityChecker(Settings())
    draft = GeneratedEmailDraft(
        subject="Status Update",
        email=(
            "Dear Team,\n\n"
            "The design phase is now complete, QA cannot proceed without the backend API, "
            "the invoice is attached, we need your availability by Monday, "
            "I enjoyed our discussion about AI tools, could we set up a quick 15‑minute call, "
            "you can view my portfolio here, and I am sorry you received the wrong report file.\n\n"
            "Best regards,\n[Your Name]"
        ),
    )
    checks = checker.run_automated_checks(
        key_facts=[
            "Design completed",
            "QA depends on it",
            "Attach invoice",
            "Ask for availability",
            "Deadline Monday",
            "Discussed AI tools",
            "Suggest 15-minute call",
            "Share portfolio link",
            "Apologize",
            "Customer reported wrong report file",
        ],
        tone="Formal",
        draft=draft,
    )

    assert checks.missing_facts == []
