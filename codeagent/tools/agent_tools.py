import asyncio
from typing import Optional
from pydantic import BaseModel, Field
from codeagent.tools.registry import tool
from codeagent.config import get_settings

class TaskArgs(BaseModel):
    goal: str = Field(..., description="The goal or task description for the sub-agent")
    context_summary: Optional[str] = Field(None, description="Relevant context summary from the parent agent to help the sub-agent")
    task_id: Optional[str] = Field(None, description="The ID of the task being executed (if part of a plan)")

@tool
async def submit_task(args: TaskArgs) -> str:
    """
    Delegate a complex task to a sub-agent.
    The sub-agent will think and act independently to achieve the goal.
    Returns the final answer from the sub-agent.
    """
    try:
        # Avoid circular imports by importing inside the function
        from codeagent.core.agent import Agent
        from codeagent.core.session import Session
        
        # Create a new session for the sub-agent
        sub_session = Session(
            system_prompt=f"You are a sub-agent working on a specific task: {args.goal}.\n"
                          "Use available tools to complete the task.\n"
                          "When finished, provide a concise summary of what you did."
        )
        
        # Create sub-agent
        # Force plan_mode=False for sub-agents to avoid infinite recursion
        settings = get_settings()
        sub_agent = Agent(settings, session=sub_session, plan_mode=False)
        
        # Run the sub-agent
        final_answer = ""
        # Pass the context_summary to the run loop
        async for chunk in sub_agent.run(args.goal, context_summary=args.context_summary):
            # For now, we just accumulate the text response
            final_answer += chunk
            
        return final_answer or "Task completed (no output)."

    except Exception as e:
        return f"Error executing sub-task: {str(e)}"
