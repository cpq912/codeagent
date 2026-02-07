# 阶段四开发计划：高级特性与优化 (Advanced & Polish)

**目标**: 提升 Agent 的搜索能力，实现子代理递归，并优化 UI 体验。
**前置条件**: 阶段三完成。
**输出**: 功能完备的 Code Agent MVP。

---

## 1. 高级搜索工具 (Advanced Search)

### 任务 1.1: Grep 工具 (`tools/search_tools.py`)
- **操作**: 实现纯 Python 版的递归搜索 (Grep)。
  - 不依赖外部 `rg` 命令，使用 `os.walk` 和 `open` 实现。
  - 处理输出截断（避免返回过多行撑爆 Token）。
- **验收标准**: 能在项目中搜索关键词，并返回文件名和行号。

### 任务 1.2: Glob 工具
- **操作**: 使用 `pathlib.glob` 实现文件模式匹配。
- **验收标准**: 能通过 `**/*.py` 找到所有 Python 文件。

---

## 2. 子代理系统 (Sub-agent System)

### 任务 2.1: Task 工具 (`tools/agent_tools.py`)
- **操作**: 实现 `submit_task(goal: str)` 工具。
  - **全异步重构**: 升级 `ToolExecutor` 和 `Agent` 以支持 `async` 工具执行。
  - 在工具内部实例化一个新的 `Agent` (Sub-agent)。
  - 创建新的 `Session` (继承 System Prompt 但清空 History)。
  - `await sub_agent.run(goal)`。
  - 返回 Sub-agent 的最终回复作为工具结果。
- **测试用例**:
  - 模拟主 Agent 调用 Task 工具，验证子 Agent 独立运行且结果能传回。
- **验收标准**: 能够处理嵌套任务。

---

## 3. UI/UX 优化 (Polish)

### 任务 3.1: Rich 渲染优化
- **操作**:
  - 使用 `Panel` 区分 User, Agent, Tool Output。
  - 为代码块添加语法高亮。
  - 为工具调用添加 "Thinking..." 动画 (Spinner)。
- **验收标准**: 界面美观，信息层级清晰。

### 3.2: 错误处理与日志
- **操作**:
  - 统一的 Error Handling，防止 Agent 因 API 错误崩溃。
  - 记录 `agent.log` 便于调试。

---

## 4. 最终验收 (Final Acceptance)
- [ ] 完成所有单元测试和集成测试。
- [ ] 进行一场完整的编程任务演练（例如：让 Agent 写一个贪吃蛇游戏）。
  - 创建文件 -> 编写代码 -> 运行报错 -> 读取错误 -> 修正代码 -> 运行成功。
