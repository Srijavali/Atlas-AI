from unittest.mock import AsyncMock

import pytest

from backend.modules.brain.service import AtlasAgent


@pytest.mark.asyncio
async def test_agent_generates_response():
    llm = AsyncMock()
    llm.generate.return_value = "Atlas is working."

    agent = AtlasAgent(llm=llm)

    result = await agent.respond(
        text="Hello Atlas",
        user_context={
            "role": "student",
            "interests": ["AI", "software engineering"],
        },
    )

    assert result == "Atlas is working."

    llm.generate.assert_awaited_once()

    prompt = llm.generate.await_args.kwargs["prompt"]

    assert "Hello Atlas" in prompt
    assert "student" in prompt
    assert "AI" in prompt


@pytest.mark.asyncio
async def test_agent_rejects_empty_text():
    llm = AsyncMock()

    agent = AtlasAgent(llm=llm)

    with pytest.raises(ValueError):
        await agent.respond(text="   ")