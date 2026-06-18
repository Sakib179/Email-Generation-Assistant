import pytest
import httpx

from backend.app.config import Settings
from backend.app.llm_gateway import GroqGateway, LLMGatewayError


@pytest.mark.asyncio
async def test_gateway_returns_clear_error_when_api_key_missing():
    settings = Settings(GROQ_API_KEY=None)
    gateway = GroqGateway(settings)

    with pytest.raises(LLMGatewayError) as exc:
        await gateway.chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0,
            max_tokens=10,
        )

    assert "Groq API key is not configured" in exc.value.public_message


def test_gateway_extracts_retry_after_from_groq_message():
    response = httpx.Response(429, headers={}, json={"error": {"message": "Rate limit reached. Please try again in 7.85s."}})
    detail = GroqGateway._extract_error_detail(response)

    assert GroqGateway._extract_retry_after_seconds(response, detail) == 7.85
