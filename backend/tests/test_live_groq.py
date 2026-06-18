import os

import pytest

from backend.app.config import Settings
from backend.app.llm_gateway import GroqGateway


@pytest.mark.asyncio
async def test_live_groq_completion_when_enabled():
    if os.getenv("RUN_LIVE_LLM_TESTS") != "true" or not os.getenv("GROQ_API_KEY"):
        pytest.skip("Live Groq test disabled.")

    settings = Settings()
    gateway = GroqGateway(settings)
    result = await gateway.chat_completion(
        messages=[
            {"role": "system", "content": "Return only JSON."},
            {"role": "user", "content": "{\"ok\": true}"},
        ],
        temperature=0,
        max_tokens=50,
    )

    assert result.content
    assert result.model_used

