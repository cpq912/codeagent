# 详细设计文档 - v1.2 Plan Mode & Context Monitor

**版本**: v1.1 (Draft)
**日期**: 2026-02-08
**关联文档**:
- 需求文档v1 (FRD)
- 技术方案设计v1.1 (Architecture)

---

## 1. 概述
本版本旨在引入两个核心能力，以增强 CodeAgent 处理复杂长任务的能力：
1.  **Plan Mode (任务规划)**：允许 Agent 将复杂目标拆解为有依赖关系的子任务图 (DAG)，并有序执行。
2.  **Context Monitor (上下文管理)**：实时监控 Token 使用量，并在临界点进行智能压缩，防止 Context Window 溢出。

---

## 2. 模块设计：Task Management (Plan Mode)

### 2.1 核心概念
*   **Plan Mode**: Agent 的一种运行模式。开启时，Agent 不直接执行操作，而是先生成任务列表，然后逐个调度。
*   **TaskManager**: 负责维护任务状态、依赖关系和执行结果的内存组件。
*   **Task**: 单个任务单元，包含 ID、描述、状态、依赖、结果。

### 2.2 数据结构 (Data Structures)

#### Task Schema
```python
class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class Task(BaseModel):
    id: str
    description: str
    dependencies: List[str] = [] # 依赖的 Task IDs
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None # 执行结果摘要
    error: Optional[str] = None  # 错误信息
```

#### TaskManager Interface
```python
class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.execution_queue: List[str] = [] # 拓扑排序后的执行顺序

    def create_plan(self, tasks: List[Dict]):
        """初始化任务列表，进行依赖检查和拓扑排序"""
        pass

    def get_next_task(self) -> Optional[Task]:
        """获取下一个状态为 PENDING 且依赖全 COMPLETED 的任务"""
        pass

    def update_task(self, task_id: str, status: TaskStatus, result: str = None):
        """更新任务状态。如果 FAILED，可能需要标记下游任务为 SKIPPED"""
        pass
    
    def get_plan_summary(self) -> str:
        """生成给 LLM 看的当前计划状态摘要"""
        # Format:
        # [X] Task 1: Create file (Result: Done)
        # [>] Task 2: Implement logic (In Progress)
        # [ ] Task 3: Test
        pass
```

### 2.3 交互流程 (Interaction Flow)

1.  **初始化**: 用户输入 "帮我重构 auth 模块"。
2.  **规划阶段**:
    *   Main Agent (Plan Mode) 分析需求。
    *   调用 `create_plan` 工具，传入任务列表：
        *   Task 1: "Analyze existing auth code"
        *   Task 2: "Design new Token schema" (deps: [1])
        *   Task 3: "Implement login" (deps: [2])
3.  **执行循环 (Automated Loop)**:
    *   `TaskManager` 自动找到下一个可执行的 Task 1。
    *   Main Agent 收到提示: "Current Task: Analyze... (ID: 1)"。
    *   Main Agent 调用 `submit_task(goal="Analyze...", task_id="1")` (Sub-agent)。
    *   **自动状态流转**:
        *   若 Sub-agent 成功返回: 系统底层自动调用 `TaskManager.update_task(1, COMPLETED, result)`.
        *   若 Sub-agent 抛出异常: 系统自动标记 `FAILED`。
    *   Main Agent 仅在需要**干预**（如重试失败任务、修改后续计划）时，才主动调用 `update_task` 或 `plan_task`。
    *   循环继续。

### 2.4 新增工具 (New Tools)

#### `plan_task`
*   **Description**: Create or overwrite the current task plan.
*   **Args**:
    *   `tasks`: List of `{id, description, dependencies}`.

#### `update_task_status`
*   **Description**: Update the status of a task.
*   **Args**:
    *   `task_id`: str
    *   `status`: "completed" | "failed"
    *   `result`: str (summary of what was done)

---

## 3. 模块设计：Context Monitor

### 3.1 核心逻辑
基于 `技术方案设计v1.1` 的定义：
*   `Effective Window` = `Model Max` - `Reserved Output` (e.g. 200k - 8k = 192k)。
*   `Usage Ratio` = `Current` / `Effective`。

### 3.2 压缩策略 (Compression Strategy)

当 `Usage Ratio > 0.9` (即 > 172k tokens) 时触发：

1.  **Identify Boundary**: 找到上一次压缩的边界 `last_boundary`。
2.  **Target Range**: 选择从 `last_boundary` 到 `Current - 10 (Last N messages)` 的消息。
3.  **Summarize**:
    *   调用 LLM (可以是便宜的模型，如 Haiku) 对 Target Range 进行摘要。
    *   Prompt: "Summarize the following conversation history, focusing on key decisions, tool outputs, and current state. Preserve file paths and critical code snippets."
4.  **Replace**:
    *   创建一个新的 `Message(role="system", content="<Previous Context Summary>: ...")`。
    *   移除 Target Range 的原始消息。
    *   插入 Summary Message。
5.  **Update Boundary**: 更新 `last_boundary` 指向 Summary Message 之后。

### 3.3 实现类图
```python
class Session:
    # ... existing ...
    
    async def compress_context(self, llm: LLMClient):
        if self.token_usage_ratio() < 0.9:
            return
            
        # 1. Slice messages
        preserve_count = 10
        to_compress = self.messages[self.compression_boundary : -preserve_count]
        
        if not to_compress:
            return

        # 2. Generate Summary
        summary = await llm.generate_summary(to_compress)
        
        # 3. Reconstruct
        new_messages = (
            self.messages[:self.compression_boundary] + 
            [Message.system(f"Summary: {summary}")] + 
            self.messages[-preserve_count:]
        )
        
        self.messages = new_messages
        self.compression_boundary = len(new_messages) - preserve_count - 1
```

---

## 4. 开发计划 (Implementation Plan)

### Phase 1: Context Monitor (P0)
1.  集成简单的字符估算器 (`len(text)/4`)，作为 `tiktoken` 的轻量级替代方案。
2.  实现 `Session.token_usage_ratio`。
3.  实现 `Session.compress_context` (Mock summary generation first)。
4.  在 `Agent.run` 循环中插入检查点。

### Phase 2: Task Manager (P1)
1.  实现 `TaskManager` 类 (纯逻辑，无 LLM)。
2.  实现 `plan_task` 和 `update_task_status` 工具。
3.  集成到 `Agent` 中，当 `plan_mode=True` 时加载这些工具。

### Phase 3: Integration Test
1.  测试 Case: 给 Agent 一个超长任务（生成大量 Token），验证是否触发压缩且逻辑不中断。
2.  测试 Case: 给 Agent 一个复杂任务（Plan Mode），验证是否能生成计划并依序执行。

---

## 5. 验收标准 (Acceptance Criteria)
1.  **Context**: 当模拟历史超过 90% 时，日志显示触发压缩，且后续对话能引用之前的摘要信息。
2.  **Plan**: Agent 能够针对 "写一个贪吃蛇游戏" 这样的任务，自动拆解为 "创建文件" -> "写代码" -> "测试" 三个步骤，并按顺序执行。
