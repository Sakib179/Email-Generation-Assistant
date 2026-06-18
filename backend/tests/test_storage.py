from backend.app.schemas import GenerationLogRecord, QualityScores
from backend.app.storage import Storage


def test_storage_deletes_history_item(tmp_path):
    storage = Storage(tmp_path / "history.db")
    record = GenerationLogRecord(
        intent="Follow up after meeting",
        key_facts=["Meeting was yesterday"],
        tone="Formal",
        strategy="advanced",
        model_used="test-model",
        subject="Follow-Up",
        email="Dear [Recipient],\n\nThank you for meeting yesterday.\n\nBest regards,\n[Your Name]",
        quality_scores=QualityScores(
            fact_recall_integration=10,
            tone_audience_fit=9,
            professional_email_quality=9,
            overall=9.33,
        ),
        included_facts=["Meeting was yesterday"],
        missing_facts=[],
        attempt_count=1,
        needs_human_review=False,
        review_reasons=[],
        hallucination_flag=False,
        judge_reason="Test record.",
        prompt_version="test-v1",
        token_usage={},
        latency_ms=12.0,
    )

    storage.save_generation(record)
    item = storage.list_history(limit=1)[0]

    assert storage.delete_history_item(item.id) is True
    assert storage.list_history(limit=1) == []
    assert storage.delete_history_item(item.id) is False
