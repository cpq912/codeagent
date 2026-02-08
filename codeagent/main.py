import sys
import os
from pydantic import ValidationError
from rich.console import Console

from codeagent.config import get_settings
from codeagent.cli.repl import run_repl

console = Console()

def main():
    try:
        # Load configuration
        settings = get_settings()
        
        # Parse plan mode from CLI flag or environment
        argv = sys.argv[1:]
        plan_mode = ("--plan" in argv) or (os.environ.get("CODEAGENT_PLAN_MODE", "").strip() in ("1", "true", "True"))
        
        # Start REPL
        run_repl(settings, plan_mode=plan_mode)
        
    except ValidationError as e:
        console.print("[bold red]Configuration Error:[/bold red]")
        console.print(str(e))
        console.print("\n[yellow]Hint: Copy .env.example to .env and fill in your API keys.[/yellow]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")
        sys.exit(0)

if __name__ == "__main__":
    main()
