import asyncio
from pydantic import BaseModel, Field
from codeagent.tools.registry import tool
from codeagent.config import get_settings

class TaskArgs(BaseModel):
    goal: str = Field(..., description="The goal or task description for the sub-agent")

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
        settings = get_settings()
        sub_agent = Agent(settings, session=sub_session)
        
        # Run the sub-agent
        final_answer = ""
        async for chunk in sub_agent.run(args.goal):
            # For now, we just accumulate the text response
            # In a real UI, we might want to stream sub-agent thoughts too
            final_answer += chunk
            
        return final_answer or "Task completed (no output)."

    except Exception as e:
        return f"Error executing sub-task: {str(e)}"
