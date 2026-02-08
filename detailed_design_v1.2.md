# 详细设计文档 - v1.2 统一 Shell 执行层

**版本**: v1.2 (Draft)
**日期**: 2026-02-09
**关联文档**:
- detailed_design_v1.1.md (任务规划 & 上下文监控)
- FRD v1.2 (Shell 需求)

---

## 1. 概述
CodeAgent 目前缺乏原生的 Shell 执行能力，这限制了它以下方面的能力：
1.  运行测试或脚本。
2.  使用高效的系统工具（如 grep, find）进行上下文收集。
3.  支持子代理执行代码。

本版本 (v1.2) 引入了一个统一的 **Shell 执行层 (Shell Execution Layer)** 来填补这一空白。

**注意**: *智能上下文提取 (Smart Context Extraction)* 和 *混合代理模式 (Hybrid Agent Model)* 等高级功能将推迟到 v1.3，因为它们依赖于此 Shell 能力。

---

## 2. 模块设计：ShellExecutor

### 2.1 架构
`ShellExecutor` 是位于 `core` 层的单例服务。它充当操作系统 Shell 的网关，确保内部系统调用和外部 LLM 工具调用的一致性和安全性。

```mermaid
graph TD
    A[LLM Tool Call (run_shell)] --> C[ShellExecutor]
    B[Internal System Logic] --> C
    C --> D{Security Check}
    D -- Pass --> E[Subprocess (Popen)]
    D -- Fail --> F[Raise SecurityError]
    E --> G[OS Shell (PowerShell/Bash)]
```

### 2.2 类设计

#### `ShellExecutor` (core/shell.py)
```python
import subprocess
import platform
import os
from typing import Optional, List

class CommandResult:
    stdout: str
    stderr: str
    exit_code: int
    duration: float

class ShellExecutor:
    @staticmethod
    def _detect_shell() -> List[str]:
        """
        返回 Shell 命令前缀。
        Windows -> ["powershell", "-Command"]
        Linux/Mac -> ["/bin/bash", "-c"]
        """
        pass

    @staticmethod
    def run(command: str, cwd: str = None, timeout: int = 60) -> CommandResult:
        """
        执行 Shell 命令。
        
        安全性:
        - 拦截危险关键字 (rm -rf 等)
        - 强制 CWD 必须在项目根目录（或特定允许路径）内。
        
        Args:
            command: 命令字符串。
            cwd: 工作目录。默认为项目根目录。
            timeout: 最大执行时间（秒）。
        """
        pass
```

### 2.3 工具集成

#### `run_shell` Tool (tools/shell_tools.py)
此工具将 `ShellExecutor` 暴露给 LLM 使用。

*   **Name**: `run_shell`
*   **Description**: 在宿主机上执行 Shell 命令。
*   **Parameters**:
    *   `command` (str): 要执行的命令。
*   **Output**: 组合后的 stdout/stderr 字符串，或错误信息。

---

## 3. 安全策略

### 3.1 黑名单 (Blacklist)
以下模式必须在 `ShellExecutor` 层面被拦截：
*   `rm -rf /` (及变体)
*   `Format-Volume` (Windows)
*   `dd if=/dev/zero`
*   `:(){:|:&};:` (Fork bomb)

### 3.2 目录锁定 (Directory Locking)
*   所有命令默认在 `os.getcwd()` (项目根目录) 执行。
*   如果提供了 `cwd`，必须验证其为项目根目录的子目录。

### 3.3 交互式命令
*   需要 stdin 输入的命令（如 `python` REPL, `nano`）会挂起。
*   **缓解措施**: `timeout` 参数（默认 60s）确保进程如果不结束会被杀死。输出将捕获超时前打印的所有内容。

---

## 4. 开发计划

### Phase 1: 核心实现 (P0)
1.  创建 `codeagent/core/shell.py`。
2.  实现 `ShellExecutor` 及跨平台检测 (Windows/Linux)。
3.  实现基础安全检查（黑名单）。

### Phase 2: 工具集成 (P0)
1.  创建 `codeagent/tools/shell_tools.py`。
2.  在 `agent.py` 中注册 `run_shell` 工具。

### Phase 3: 测试 (P1)
1.  `ShellExecutor` 的单元测试（Mock subprocess）。
2.  集成测试：`manual_test_shell.py` 执行 `echo hello` 和 `dir`。

---

## 5. 验收标准
1.  **Windows 支持**: CodeAgent 在 Windows 上运行时可以通过 `run_shell` 执行 `dir` 或 `Get-ChildItem`。
2.  **安全性**: 尝试执行 `rm -rf /` (或 Mock 等效命令) 返回 "Blocked" 错误，且不执行。
3.  **超时**: 运行 `python -c "import time; time.sleep(10)"` 并设置 timeout=2，能正确杀死进程并返回超时信息。
