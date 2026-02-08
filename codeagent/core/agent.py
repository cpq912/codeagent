from typing import Optional, AsyncGenerator
import logging
import json

from codeagent.core.session import Session
from codeagent.core.llm import LLMClient
from codeagent.core.message import Message
from codeagent.config import Settings
from codeagent.tools.registry import ToolRegistry
from codeagent.core.executor import ToolExecutor
from codeagent.core.task_manager import TaskManager, TaskStatus
from codeagent.core.context import current_task_manager

# Import tools to ensure they are registered
import codeagent.tools.file_tools
import codeagent.tools.search_tools
import codeagent.tools.agent_tools
import codeagent.tools.task_tools
import codeagent.tools.shell_tools

logger = logging.getLogger(__name__)

class Agent:
    """
    Core Agent class that manages the Think-Act loop.
    """
    def __init__(self, settings: Settings, session: Optional[Session] = None, plan_mode: bool = False):
        self.settings = settings
        self.session = session or Session()
        self.llm = LLMClient(settings)
        self.plan_mode = plan_mode
        # Load tools
        self.tools_schema = ToolRegistry.get_schemas()
        
        # Initialize TaskManager if plan_mode is True
        self.task_manager = TaskManager() if plan_mode else None

    async def run(self, user_input: str, context_summary: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        Main execution loop (Think -> Act -> Observe -> Think).
        
        Args:
            user_input: The user's input string.
            context_summary: Optional summary of previous context (for sub-agents).
            
        Yields:
            str: The response text from the LLM.
        """
        # Set context variable for tools
        token = None
        if self.task_manager:
            token = current_task_manager.set(self.task_manager)

        try:
            resolved = await self.session.resolve_reference(user_input)
            if resolved:
                user_input = f"{user_input}\n\n{resolved}"
            self.session.add_message(Message.user(user_input))
            
            # Inject context if provided (for sub-agents)
            if context_summary:
                self.session.inject_context(context_summary)
            
            while True:
                # 0. Context Monitor & Compression
                # Check and compress if needed before calling LLM
                await self.session.compress_context(self.llm)

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
                    tool_names = []
                    for tc in response_msg.tool_calls:
                        try:
                            n = tc.get("function", {}).get("name")
                        except Exception:
                            n = None
                        tool_names.append(n or "unknown")
                    yield f"\n[Executing {len(response_msg.tool_calls)} tool calls: {', '.join(tool_names)}]\n"
                    
                    # Execute Tools
                    results = await ToolExecutor.execute(response_msg.tool_calls)
                    
                    # Add Tool Results to History
                    for res in results:
                        # === Task Automation Logic ===
                        if self.task_manager and res["name"] == "submit_task":
                            # Find which tool call triggered this result
                            call_args = None
                            for tc in response_msg.tool_calls:
                                if tc["id"] == res["tool_call_id"]:
                                    try:
                                        call_args = json.loads(tc["function"]["arguments"])
                                    except Exception as e:
                                        logger.warning(f"Failed to parse args for task automation: {e}")
                                    break
                            
                            if call_args and "task_id" in call_args and call_args["task_id"]:
                                task_id = call_args["task_id"]
                                # Check if success or failure
                                # Simple heuristic: if content starts with "Error", it failed
                                if res["content"].startswith("Error"):
                                    try:
                                        self.task_manager.update_task(task_id, TaskStatus.FAILED, error=res["content"])
                                    except Exception:
                                        pass # Ignore invalid task IDs
                                else:
                                    try:
                                        self.task_manager.update_task(task_id, TaskStatus.COMPLETED, result=res["content"])
                                    except Exception:
                                        pass
                                
                                # Append plan summary to tool output so Agent sees updated state
                                # Auto-Chaining: Check for next task and prompt Agent
                                next_task = self.task_manager.get_next_task()
                                if next_task:
                                    res["content"] += f"\n\n[System] Task {task_id} completed. The next task is: {next_task.description} (ID: {next_task.id}). Please proceed with it."
                                else:
                                    res["content"] += f"\n\n[System] Task {task_id} completed. No pending tasks found."
                                
                                res["content"] += "\n" + self.task_manager.get_plan_summary()

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
        finally:
            # Clean up context var
            if token:
                current_task_manager.reset(token)
