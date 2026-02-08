from codeagent.tools.registry import tool
from codeagent.core.shell import ShellExecutor
from pydantic import BaseModel, Field

class RunShellInput(BaseModel):
    command: str = Field(..., description="The shell command to execute (e.g., 'python script.py', 'grep pattern .')")

@tool
def run_shell(args: RunShellInput) -> str:
    """Execute a shell command on the host machine. Use this to run scripts, tests, or system tools."""
    """
    Executes a shell command via the unified ShellExecutor.
    """
    result = ShellExecutor.run(args.command)
    
    output_parts = []
    if result.stdout:
        output_parts.append(f"STDOUT:\n{result.stdout}")
    if result.stderr:
        output_parts.append(f"STDERR:\n{result.stderr}")
    
    if result.exit_code != 0:
        output_parts.append(f"\n[Exit Code: {result.exit_code}]")
    
    output = "\n".join(output_parts)
    
    if not output:
        output = "[Command finished with no output]"
        
    # Simple truncation to avoid blowing up context immediately
    MAX_LEN = 5000
    if len(output) > MAX_LEN:
         output = output[:MAX_LEN] + f"\n... [Output Truncated, total length {len(output)} chars]"
         
    return output
