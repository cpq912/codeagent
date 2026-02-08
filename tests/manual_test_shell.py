import asyncio
import os
import sys

# Ensure we can import codeagent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from codeagent.core.shell import ShellExecutor
from codeagent.tools.shell_tools import run_shell, RunShellInput

def test_internal_execution():
    print("\n=== Test 1: Internal ShellExecutor ===")
    
    # 1. Basic
    print("Running 'echo hello'...")
    res = ShellExecutor.run("echo hello")
    print(f"Stdout: {res.stdout.strip()}")
    assert "hello" in res.stdout
    
    # 2. Blacklist
    print("Running blocked command 'rm -rf /'...")
    res = ShellExecutor.run("rm -rf /")
    print(f"Stderr: {res.stderr}")
    assert "blocked" in res.stderr
    
    # 3. Timeout
    print("Running slow command with timeout...")
    if os.name == 'nt':
        cmd = "Start-Sleep -Seconds 3"
    else:
        cmd = "sleep 3"
        
    res = ShellExecutor.run(cmd, timeout=1)
    print(f"Result: {res}")
    assert "TimeoutError" in res.stderr

def test_tool_execution():
    print("\n=== Test 2: Tool Wrapper (run_shell) ===")
    
    # 1. Normal usage
    cmd = "dir" if os.name == 'nt' else "ls"
    inp = RunShellInput(command=cmd)
        
    out = run_shell(inp)
    print("Tool Output (Partial):")
    print(out[:200])
    assert "STDOUT" in out

if __name__ == "__main__":
    test_internal_execution()
    test_tool_execution()
    print("\nAll Shell tests passed!")
