import pytest
from unittest.mock import AsyncMock, MagicMock
from codeagent.core.agent import Agent
from codeagent.core.message import Message

@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.openai_api_key = "test"
    settings.openai_base_url = "http://test"
    settings.openai_model = "test"
    return settings

@pytest.mark.asyncio
async def test_agent_run(mock_settings):
    agent = Agent(mock_settings)
    
    # Mock LLM response
    mock_response = Message.assistant("Hello User")
    agent.llm.chat = AsyncMock(return_value=mock_response)
    
    # Run agent
    responses = []
    async for chunk in agent.run("Hi"):
        responses.append(chunk)
        
    # Verify interaction
    assert len(responses) == 1
    assert responses[0] == "Hello User"
    
    # Verify Session state
    assert len(agent.session.history) == 3 # System + User + Assistant
    assert agent.session.history[1].content == "Hi"
    assert agent.session.history[2].content == "Hello User"
