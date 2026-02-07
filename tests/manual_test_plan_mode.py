import asyncio
import os
from codeagent.config import Settings
from codeagent.core.agent import Agent

async def run_test():
    print("=== Plan Mode Real LLM Test ===\n")
    
    # 1. Setup (Requires .env with API Key)
    try:
        settings = Settings()
    except Exception as e:
        print(f"Error loading settings: {e}")
        print("Please ensure .env file exists with valid API keys.")
        return

    # Enable Plan Mode
    agent = Agent(settings, plan_mode=True)
    
    # 2. Define a multi-step task
    # A simple math problem that requires steps: 
    # 1. Create a python file with a sum function.
    # 2. Create a test file.
    # 3. Run the test.
    # This forces the agent to plan and execute sequentially.
    task_prompt = (
        "I need you to implement a simple Python function `add(a, b)` in `test_math.py` "
        "and then run a test to verify `add(1, 2) == 3`. "
        "Please plan this task first, then execute it step by step."
    )
    
    print(f"User Prompt: {task_prompt}\n")
    print("-" * 50)

    # 3. Run Agent
    # We will print the output chunks to see the thought process
    async for chunk in agent.run(task_prompt):
        print(chunk, end="", flush=True)

    print("\n" + "-" * 50)
    print("=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(run_test())
