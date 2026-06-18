from backend.app.prompt_templates import build_generation_messages
from backend.app.schemas import StrategyName


def test_advanced_prompt_contains_all_facts_and_tone():
    facts = ["Meeting was yesterday", "Proposal due Friday", "Client asked for timeline"]
    bundle = build_generation_messages(
        intent="Follow up after client meeting",
        key_facts=facts,
        tone="Formal",
        strategy=StrategyName.advanced,
        prompt_version="test-v1",
    )
    joined = "\n".join(message["content"] for message in bundle.messages)

    for fact in facts:
        assert fact in joined
    assert "Formal" in joined
    assert "Return only valid JSON" in joined
    assert "senior executive communication specialist" in joined


def test_simple_prompt_contains_all_facts_and_tone():
    facts = ["Need pricing breakdown", "Deadline Monday"]
    bundle = build_generation_messages(
        intent="Request missing proposal details",
        key_facts=facts,
        tone="Polite and clear",
        strategy=StrategyName.simple,
        prompt_version="test-v1",
    )
    joined = "\n".join(message["content"] for message in bundle.messages)

    for fact in facts:
        assert fact in joined
    assert "Polite and clear" in joined
    assert "Write a professional English email" in joined

