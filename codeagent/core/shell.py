import subprocess
import os
import platform
import logging
import time
import re
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
        if platform.system() == "Windows":
            command = "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; $OutputEncoding = [System.Text.Encoding]::UTF8; " + command
        # Prefer project virtual environment if present
        project_root = os.getcwd()
        if platform.system() == "Windows":
            venv_dir = os.path.join(project_root, ".venv", "Scripts")
            venv_python = os.path.join(venv_dir, "python.exe")
        else:
            venv_dir = os.path.join(project_root, ".venv", "bin")
            venv_python = os.path.join(venv_dir, "python")
        if platform.system() == "Windows":
            # Normalize PowerShell syntax and enforce venv python within command segments
            # 1) Replace invalid '&&' with ';'
            command = command.replace("&&", ";")
            # 2) Convert 'cd dir' to 'Set-Location dir' at segment starts
            command = re.sub(r'(^|;)\s*cd\s+', r'\1 Set-Location ', command)
            # 3) Rewrite python invocations to venv python at segment starts
            if os.path.exists(venv_python):
                def _rewrite_py(m: re.Match) -> str:
                    prefix = m.group(1) or ""
                    if prefix.strip() == "":
                        return f'& "{venv_python}" '
                    else:
                        return f'{prefix} & "{venv_python}" '
                command = re.sub(r'(^|;)\s*(?:python|py)\s', _rewrite_py, command)
        else:
            # On *nix, if venv exists and command starts with python, rewrite
            if os.path.exists(venv_python):
                command = re.sub(r'(^|;)\s*python\s', lambda m: f'{m.group(1) or ""} "{venv_python}" ', command)
        final_args = shell_cmd + [command]
        
        try:
            logger.info(f"Executing shell command: {command} in {cwd}")
            # Note: We use shell=False because we are explicitly invoking the shell executable
            # and passing the command string as an argument.
            # Prepare environment: inject venv path at the front of PATH if exists
            env = os.environ.copy()
            if os.path.isdir(venv_dir):
                env["PATH"] = venv_dir + os.pathsep + env.get("PATH", "")
                env["VIRTUAL_ENV"] = os.path.dirname(venv_dir)
            env["PYTHONUTF8"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")
            proc = subprocess.run(
                final_args,
                cwd=cwd,
                capture_output=True,
                text=True, 
                timeout=timeout,
                encoding='utf-8',
                errors='replace',
                env=env
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
