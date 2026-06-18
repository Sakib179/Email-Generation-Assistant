import pytest

from backend.app.config import Settings
from backend.app.email_service import EmailService, parse_generation_output
from backend.app.llm_gateway import LLMResult
from backend.app.quality_checker import QualityChecker
from backend.app.schemas import EmailGenerationRequest, StrategyName


class FakeGateway:
    def __init__(self):
        self.calls = 0

    async def chat_completion(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            content = """{
                "subject": "Follow-Up on Website Redesign",
                "email": "Dear [Recipient],\\n\\nThank you for meeting yesterday to discuss the website redesign. I understand you asked for a timeline.\\n\\nPlease let me know if you have any questions.\\n\\nBest regards,\\n[Your Name]",
                "included_facts": ["Meeting was yesterday", "Discussed website redesign", "Client asked for timeline"],
                "missing_facts": ["Proposal due Friday"],
                "tone_used": "Formal",
                "notes": "Initial draft."
            }"""
        else:
            content = """{
                "subject": "Follow-Up on Website Redesign Timeline",
                "email": "Dear [Recipient],\\n\\nThank you for meeting yesterday to discuss the website redesign. I understand you asked for a timeline, and I will include it in the proposal due Friday.\\n\\nPlease let me know if there is anything else you would like included.\\n\\nBest regards,\\n[Your Name]",
                "included_facts": ["Meeting was yesterday", "Discussed website redesign", "Client asked for timeline", "Proposal due Friday"],
                "missing_facts": [],
                "tone_used": "Formal",
                "notes": "Repaired draft."
            }"""
        return LLMResult(content=content, model_used="fake-model", latency_ms=10.0)


@pytest.mark.asyncio
async def test_email_service_repairs_missing_fact():
    settings = Settings()
    gateway = FakeGateway()
    checker = QualityChecker(settings)
    service = EmailService(settings=settings, gateway=gateway, quality_checker=checker)
    request = EmailGenerationRequest(
        intent="Follow up after a client meeting",
        key_facts=[
            "Meeting was yesterday",
            "Discussed website redesign",
            "Client asked for timeline",
            "Proposal due Friday",
        ],
        tone="Formal",
        strategy=StrategyName.advanced,
    )

    response = await service.generate_email(request, use_llm_judge=False)

    assert response.attempt_count == 2
    assert response.missing_facts == []
    assert "proposal due Friday" in response.email
    assert response.needs_human_review is False


def test_parse_generation_output_plain_text_fallback():
    request = EmailGenerationRequest(
        intent="Schedule an interview",
        key_facts=["Candidate shortlisted"],
        tone="Formal",
    )
    draft = parse_generation_output(
        "Subject: Interview Availability\n\nDear [Recipient],\n\nThe candidate has been shortlisted.\n\nBest regards,\n[Your Name]",
        request,
    )

    assert draft.subject == "Interview Availability"
    assert "candidate has been shortlisted" in draft.email.lower()

