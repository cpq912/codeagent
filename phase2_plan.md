# 阶段二开发计划：核心与LLM集成 (Core & LLM)

**目标**: 实现 Agent 的核心思考循环 (Think-Act Loop)，能够调用 LLM (Qwen) 并处理简单的对话。
**前置条件**: 阶段一完成。
**输出**: 具备“对话能力”的 CLI，Agent 能够根据 System Prompt 回答问题（暂无工具调用能力）。

---

## 1. 核心数据结构 (Core Data Structures)

### 任务 1.1: 定义 Message 模型 (`core/message.py`)
- **操作**: 使用 Pydantic 定义 `Message` 类。
  - 字段: `role` (user/assistant/system/tool), `content` (str), `tool_calls` (optional)。
  - 方法: `to_openai_format()` 转换为 API 所需格式。
- **测试用例 (`tests/core/test_message.py`)**:
  - 验证不同角色的消息能否正确转换格式。
- **验收标准**: 单元测试通过。

### 任务 1.2: Session 管理 (`core/session.py`)
- **操作**: 实现 `Session` 类。
  - 维护 `history: List[Message]`。
  - 提供 `add_message`, `get_history`, `clear_history` 方法。
  - (MVP暂不实现压缩，仅做简单的列表追加)。
- **测试用例 (`tests/core/test_session.py`)**:
  - 验证消息追加顺序正确。
  - 验证清空历史功能。
- **验收标准**: 单元测试通过。

---

## 2. LLM 客户端封装 (LLM Client)

### 任务 2.1: OpenAI 兼容客户端 (`core/llm.py`)
- **操作**: 封装 `LLMClient` 类。
  - 接收 `Settings` 配置。
  - 提供 `chat(messages, tools=None)` 异步方法。
  - 增加简单的重试机制 (`tenacity` 或手动 loop)。
- **测试用例 (`tests/core/test_llm.py`)**:
  - 使用 `unittest.mock` 模拟 OpenAI API 响应，验证 Client 能正确解析返回值。
  - 模拟网络错误，验证重试逻辑。
- **验收标准**: Mock 测试通过。

---

## 3. Agent 循环开发 (Agent Loop)

### 3.1: Agent 类基础 (`core/agent.py`)
- **操作**: 实现 `Agent` 类。
  - 组合 `Session` 和 `LLMClient`。
  - 实现 `run(user_input)` 方法：
    1. 将 input 转为 UserMessage 存入 Session。
    2. 调用 LLM 获取响应。
    3. 将响应存入 Session。
    4. 返回响应内容。
- **测试用例 (`tests/core/test_agent.py`)**:
  - Mock LLMClient，验证 Agent 的数据流转逻辑（Input -> Session -> LLM -> Session -> Output）。
- **验收标准**: 单元测试通过。

### 3.2: 集成到 CLI
- **操作**: 修改 `cli/repl.py`。
  - 实例化 Agent。
  - 在循环中调用 `agent.run(input)`。
  - 使用 `rich` 渲染 Agent 的回复。
- **验收标准**:
  - 配置真实的 Qwen API Key。
  - 启动程序，输入 "Hello"，能收到 LLM 的回复。

---

## 4. 阶段验收 (Phase Acceptance)
- [ ] 运行 `pytest`，覆盖 Message, Session, Agent 的核心逻辑。
- [ ] 实际连接 Qwen API 进行多轮对话测试（Context 记忆测试）。
  - 用户: "我叫 Tom"
  - Agent: "你好 Tom"
  - 用户: "我叫什么？"
  - Agent: "你叫 Tom" (验证 Session 生效)
