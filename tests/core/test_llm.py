import pytest
from unittest.mock import AsyncMock, MagicMock
from codeagent.core.llm import LLMClient
from codeagent.config import Settings

@pytest.fixture
def mock_settings():
    return Settings(
        openai_api_key="test_key",
        openai_base_url="http://test.url",
        openai_model="test-model"
    )

@pytest.mark.asyncio
async def test_chat_success(mock_settings):
    client = LLMClient(mock_settings)
    
    # Mock the OpenAI client
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_msg = MagicMock()
    
    mock_msg.content = "Hello World"
    mock_msg.tool_calls = None
    mock_choice.message = mock_msg
    mock_response.choices = [mock_choice]
    
    client.client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    result = await client.chat([{"role": "user", "content": "Hi"}])
    
    assert result.role == "assistant"
    assert result.content == "Hello World"
    assert result.tool_calls is None

@pytest.mark.asyncio
async def test_chat_with_tools(mock_settings):
    client = LLMClient(mock_settings)
    
    # Mock Tool Call
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_msg = MagicMock()
    
    # Mocking Pydantic model for tool_call
    mock_tc = MagicMock()
    mock_tc.model_dump.return_value = {"id": "call_1", "type": "function"}
    
    mock_msg.content = None
    mock_msg.tool_calls = [mock_tc]
    mock_choice.message = mock_msg
    mock_response.choices = [mock_choice]
    
    client.client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    result = await client.chat([{"role": "user", "content": "run tool"}])
    
    assert result.tool_calls is not None
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0]["id"] == "call_1"
