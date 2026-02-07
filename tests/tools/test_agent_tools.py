import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from codeagent.tools.agent_tools import submit_task, TaskArgs
from codeagent.core.message import Message

@pytest.mark.asyncio
async def test_submit_task():
    # Mock settings
    with patch("codeagent.tools.agent_tools.get_settings") as mock_get_settings:
        mock_settings = MagicMock()
        mock_get_settings.return_value = mock_settings
        
        # Mock Agent inside the tool
        with patch("codeagent.core.agent.Agent") as MockAgentClass:
            mock_agent_instance = MagicMock()
            MockAgentClass.return_value = mock_agent_instance
            
            # Setup async generator for agent.run
            async def mock_run(goal):
                yield "I have "
                yield "completed "
                yield "the task."
                
            mock_agent_instance.run = mock_run
            
            # Execute tool
            args = TaskArgs(goal="Do something")
            result = await submit_task(args)
            
            # Verify
            assert result == "I have completed the task."
            MockAgentClass.assert_called_once()
            # Verify session prompt contains goal
            call_args = MockAgentClass.call_args
            session = call_args.kwargs['session']
            assert "Do something" in session.system_prompt
