import subprocess
import os
import platform
import logging
import time
from typing import List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class CommandResult(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    duration: float

class ShellExecutor:
    # Simple blacklist to prevent obvious destructive operations
    BLACKLIST = [
        "rm -rf /",
        "rm -fr /",
        "Format-Volume",
        "dd if=/dev/zero",
        ":(){:|:&};:"
    ]

    @staticmethod
    def _detect_shell() -> List[str]:
        system = platform.system()
        if system == "Windows":
            return ["powershell", "-Command"]
        else:
            return ["/bin/bash", "-c"]

    @staticmethod
    def run(command: str, cwd: Optional[str] = None, timeout: int = 60) -> CommandResult:
        # 1. Security Check
        for blocked in ShellExecutor.BLACKLIST:
            if blocked in command:
                return CommandResult(
                    stdout="",
                    stderr=f"SecurityError: Command blocked due to restricted pattern: {blocked}",
                    exit_code=-1,
                    duration=0.0
                )
        
        # 2. CWD Resolution
        if cwd is None:
            cwd = os.getcwd()
        
        # Ensure we are not running outside project root (simple check)
        project_root = os.getcwd()
        try:
            # Resolve absolute paths
            abs_cwd = os.path.abspath(cwd)
            abs_root = os.path.abspath(project_root)
            # On Windows, paths are case-insensitive, but startswith is sensitive.
            # Normalizing case for check on Windows might be needed, but for now simple check.
            if platform.system() == "Windows":
                 abs_cwd = abs_cwd.lower()
                 abs_root = abs_root.lower()

            if not abs_cwd.startswith(abs_root):
                return CommandResult(
                    stdout="",
                    stderr=f"SecurityError: Working directory must be within project root: {abs_root}",
                    exit_code=-1,
                    duration=0.0
                )
        except Exception as e:
             return CommandResult(stdout="", stderr=f"Path resolution error: {e}", exit_code=-1, duration=0.0)

        # 3. Execution
        start_time = time.time()
        shell_cmd = ShellExecutor._detect_shell()
        
        # Construct arguments
        final_args = shell_cmd + [command]
        
        try:
            logger.info(f"Executing shell command: {command} in {cwd}")
            # Note: We use shell=False because we are explicitly invoking the shell executable
            # and passing the command string as an argument.
            proc = subprocess.run(
                final_args,
                cwd=cwd,
                capture_output=True,
                text=True, 
                timeout=timeout,
                encoding='utf-8',
                errors='replace'
            )
            duration = time.time() - start_time
            return CommandResult(
                stdout=proc.stdout,
                stderr=proc.stderr,
                exit_code=proc.returncode,
                duration=duration
            )
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return CommandResult(
                stdout="",
                stderr=f"TimeoutError: Command execution exceeded {timeout} seconds.",
                exit_code=-2,
                duration=duration
            )
        except Exception as e:
            duration = time.time() - start_time
            return CommandResult(
                stdout="",
                stderr=f"ExecutionError: {str(e)}",
                exit_code=-3,
                duration=duration
            )
