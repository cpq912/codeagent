from typing import Optional, AsyncGenerator
import logging

from codeagent.core.session import Session
from codeagent.core.llm import LLMClient
from codeagent.core.message import Message
from codeagent.config import Settings
from codeagent.tools.registry import ToolRegistry
from codeagent.core.executor import ToolExecutor
# Import tools to ensure they are registered
import codeagent.tools.file_tools
import codeagent.tools.search_tools
import codeagent.tools.agent_tools

logger = logging.getLogger(__name__)

class Agent:
    """
    Core Agent class that manages the Think-Act loop.
    """
    def __init__(self, settings: Settings, session: Optional[Session] = None):
        self.settings = settings
        self.session = session or Session()
        self.llm = LLMClient(settings)
        # Load tools
        self.tools_schema = ToolRegistry.get_schemas()

    async def run(self, user_input: str) -> AsyncGenerator[str, None]:
        """
        Main execution loop (Think -> Act -> Observe -> Think).
        
        Args:
            user_input: The user's input string.
            
        Yields:
            str: The response text from the LLM.
        """
        # 1. Add User Message
        self.session.add_message(Message.user(user_input))
        
        while True:
            # 2. Call LLM
            response_msg = await self.llm.chat(
                self.session.get_messages(), 
                tools=self.tools_schema if self.tools_schema else None
            )
            
            # 3. Add Assistant Message (Thinking/Call)
            self.session.add_message(response_msg)
            
            # 4. Check for Tool Calls
            if response_msg.tool_calls:
                # Notify user (optional yield)
                yield f"\n[Executing {len(response_msg.tool_calls)} tool calls...]\n"
                
                # Execute Tools
                results = await ToolExecutor.execute(response_msg.tool_calls)
                
                # Add Tool Results to History
                for res in results:
                    tool_msg = Message.tool(
                        tool_call_id=res["tool_call_id"],
                        content=res["content"],
                        name=res["name"]
                    )
                    self.session.add_message(tool_msg)
                    # Yield tool output for visibility
                    yield f"\n[Tool Output ({res['name']})]: {res['content']}\n"
                
                # Continue loop -> LLM will see tool outputs and generate next response
                continue
            
            # 5. No tool calls -> Final Answer
            if response_msg.content:
                yield response_msg.content
                
            break
