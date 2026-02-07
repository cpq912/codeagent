# 阶段三开发计划：工具系统实现 (Tool System)

**目标**: 实现工具注册机制、基础文件工具，并让 Agent 能够根据意图自动调用工具。
**前置条件**: 阶段二完成。
**输出**: 一个能读写文件、执行命令的完整 Agent。

---

## 1. 工具基础设施 (Tool Infrastructure)

### 任务 1.1: 工具定义与注册 (`tools/base.py`, `tools/registry.py`)
- **操作**:
  - 定义 `Tool` 协议/基类。
  - 实现 `@tool` 装饰器：自动提取函数签名、Docstring，生成 JSON Schema。
  - 实现 `ToolRegistry`：单例模式，管理所有注册的工具。
- **测试用例 (`tests/tools/test_registry.py`)**:
  - 定义一个简单的 `add(a: int, b: int)` 函数，使用 `@tool` 装饰。
  - 验证 Registry 能获取到该工具，且生成的 Schema 符合 OpenAI Function Calling 规范。
- **验收标准**: 单元测试通过。

### 1.2: 基础文件工具 (`tools/file_tools.py`)
- **操作**: 实现以下工具：
  - `read_file(path)`: 读取文件内容。
  - `write_file(path, content)`: 写入文件。
  - `list_dir(path)`: 列出目录。
- **验收标准**: 每个工具都能独立运行，并正确处理 FileNotFoundError 等异常。

---

## 2. Agent 工具调用逻辑 (Tool Execution Loop)

### 任务 2.1: 增强 LLM Client
- **操作**: 修改 `core/llm.py`，支持传入 `tools` 参数（从 Registry 获取 Schema）。
- **验收标准**: 能够向 API 发送包含 `tools` 定义的请求。

### 任务 2.2: 实现工具执行器 (`core/executor.py`)
- **操作**: 实现 `ToolExecutor`。
  - 接收 `ToolCall` 对象。
  - 解析参数，查找对应函数并执行。
  - 捕获执行结果或异常，格式化为字符串。
- **测试用例**:
  - 模拟一个 ToolCall，验证 Executor 能正确调用函数并返回结果。

### 任务 2.3: 升级 Agent 循环 (`core/agent.py`)
- **操作**: 将 `run` 方法升级为 `Think-Act` 循环。
  - **While True**:
    1. Call LLM。
    2. Check `tool_calls`?
       - No -> Break & Return text.
       - Yes -> `ToolExecutor.execute()` -> Add ToolMessage to Session -> Continue Loop.
- **验收标准**:
  - Agent 能够自动执行：User "Create a file named test.txt" -> Agent Call `write_file` -> Agent Reply "File created".

---

## 3. 权限与安全 (Security)

### 任务 3.1: 权限拦截策略
- **操作**:
  - 在 `config.py` 定义 `PERMISSION_POLICY` (Map<ToolName, Action>)。
    - `read_file`: ALLOW
    - `write_file`: CONFIRM
  - 在 `ToolExecutor` 中加入检查逻辑。
    - 如果是 CONFIRM，调用 CLI 提示用户。
- **验收标准**: 尝试写入文件时，终端提示 "Allow execution? [y/n]"。

---

## 4. 阶段验收 (Phase Acceptance)
- [ ] 自动化测试覆盖工具注册、Schema 生成逻辑。
- [ ] 端到端测试：
  - 任务: "查看当前目录下的文件，然后创建一个名为 hello.txt 的文件，内容是 world"
  - 预期:
    1. Agent 调用 `list_dir`。
    2. Agent 调用 `write_file` (触发确认提示)。
    3. 验证磁盘上文件创建成功。
