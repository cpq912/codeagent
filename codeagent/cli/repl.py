import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from codeagent.core.agent import Agent

console = Console()

style = Style.from_dict({
    'prompt': 'ansicyan bold',
})

def run_repl(settings, plan_mode: bool = False):
    """
    Start the Read-Eval-Print Loop with Agent integration.
    """
    # Initialize Agent
    agent = Agent(settings, plan_mode=plan_mode)
    
    session = PromptSession(style=style)
    
    console.print(Panel(f"[bold green]CodeAgent CLI[/bold green]\nModel: {settings.openai_model}\nPlan Mode: {'ON' if plan_mode else 'OFF'}", border_style="green"))
    console.print("Type 'exit' or 'quit' to close.")
    
    # We need an event loop for async Agent
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        while True:
            try:
                user_input = session.prompt([('class:prompt', '\nCodeAgent >> ')])
                
                if user_input.strip().lower() in ('exit', 'quit'):
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                    
                if not user_input.strip():
                    continue
                
                # Show spinner while thinking
                with console.status("[bold green]Thinking...[/bold green]", spinner="dots"):
                    # Execute Agent asynchronously
                    loop.run_until_complete(agent_run_wrapper(agent, user_input))

            except KeyboardInterrupt:
                continue
            except EOFError:
                break
    finally:
        loop.close()

async def agent_run_wrapper(agent, user_input):
    """Helper to run async generator until completion and render outputs."""
    final_response = ""
    
    async for chunk in agent.run(user_input):
        # Detect if chunk is a structured notification (simple heuristic for MVP)
        if chunk.startswith("\n[Executing"):
            # Tool Execution Notification
            console.print(Panel(Text(chunk.strip(), style="bold yellow"), title="Tool Execution", border_style="yellow"))
        elif chunk.startswith("\n[Tool Output"):
            # Tool Output
            console.print(Panel(Text(chunk.strip(), style="dim"), title="Tool Output", border_style="white"))
        else:
            # Main LLM Content part
            final_response += chunk
            
    # Render final response
    if final_response:
        console.print(Panel(Markdown(final_response), title="Agent", border_style="blue"))
