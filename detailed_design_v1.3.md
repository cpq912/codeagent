# 详细设计文档 - v1.3 智能上下文与混合任务增强

**版本**: v1.3  
**日期**: 2026-02-09  
**关联文档**:  
- CHANGELOG v1.3 (Smart Context & Hybrid Task)  
- 技术方案设计 v1.3 (Agent 预处理、Task 参数增强)  
- FRD v1.3 (功能点 1.3 与子代理初始化增强)  
- detailed_design_v1.2.md (统一 Shell 执行层)

---

## 1. 概述
v1.3 在 v1.2 统一 Shell 能力基础上，新增两项核心能力：
1. 智能上下文显式提取 (Smart Context Extractor)：用户通过 `@file:keyword` 显式提供线索，系统自动定位并读取相关文件，以结构化片段追加到当前消息，降低初始探索成本。
2. 混合任务模型增强 (Hybrid Task Model)：拓展 `Task` 工具参数，允许主代理以 Technical Lead 角色向子代理提供 `resources` 与 `hints`，使子代理快速聚焦上下文并提升执行效率。

这两项能力均遵循现有的安全与上下文管理策略，并与既有 Agent 循环无缝集成。

---

## 2. 模块设计

### 2.1 智能上下文显式提取 (Smart Context Extractor)
**目标**: 将用户输入中的显式文件线索转化为可消费的上下文，减少无目标的初始检索。

**输入格式**: `@file:keyword`（示例：`@file:agent`、`@file:src/core/session.py`）

**核心流程**:
1. 解析关键字：从用户输入中提取 `@file:` 后的内容（支持多个引用）。
2. 文件定位：
   - 优先尝试精确路径匹配（如包含 `/` 或 `\` 的路径）。
   - 其次进行 Glob 模式匹配（如 `**/session.py`、`**/*agent*`）。
3. 读取内容：
   - 对唯一匹配：读取该文件内容。
   - 对多项匹配：依次读取每个文件内容。
   - 对无匹配：生成警告片段提示未匹配。
4. 结构化注入：将读取结果封装为 `<Context><File path="...">...</File></Context>`，以字符串追加到 UserMessage。
5. 限流与安全：
   - 限制最大读取字节与行数（如 1000 行/200KB），超出则截断并标注。
   - 仅允许项目根目录子路径。

**集成位置**:
- `core/session.py`: `resolve_reference(input_text: str) -> str`  
  返回结构化上下文字符串（如无引用或未匹配，返回空字符串）。
- `core/agent.py`: `Agent.run(...)`  
  在写入用户消息前调用 `resolve_reference` 并将结果拼接追加。

**输出格式示例**:
```xml
<Context>
  <File path="codeagent/core/session.py">
    <![CDATA[
    class Session:
        ...
    ]]>
  </File>
  <File path="codeagent/core/agent.py">
    <![CDATA[
    class Agent:
        ...
    ]]>
  </File>
</Context>
```

---

### 2.2 混合任务模型增强 (Hybrid Task Model)
**目标**: 让主代理在创建子代理时显式提供上下文线索，减少子代理的冷启动探索时间。

**参数扩展**:
- `Task` 工具新增可选参数：
  - `resources: List[str]`（文件路径或目录）
  - `hints: str`（实现建议/技术要点）

**集成位置**:
- `tools/agent_tools.py`：更新 `Task` 的 Pydantic 输入模型与装饰器元数据。
- `core/agent.py`：
  - Main Agent 触发 `Task` 时，读取 `resources` 与 `hints`。
  - 创建 Sub-agent 时，将上述线索整合进其 System Prompt 或初始化上下文。
  - 约束：Sub-agent 默认关闭 `plan_mode`，专注单一目标执行。

**运行约束与策略**:
- 子代理计划模式约束：遵循“Sub-agent Plan Mode Constraint”，避免递归规划膨胀。
- 上下文传递策略：
  - 主代理优先生成简短 `context_summary`（最近相关交互摘要）。
  - 与 `resources`、`hints` 一并注入子代理初始上下文。
- 任务状态自动化（参考 FRD 规则）：
  - 若子代理成功返回且无错误，自动标记对应任务为完成，并推进后续任务。

---

## 3. 类设计与接口

### 3.1 Session（上下文解析与压缩）
**新增方法**:
- `async def resolve_reference(self, input_text: str) -> str`  
  功能：解析 `@file:keyword`，完成匹配与读取，返回结构化上下文字符串。
  规则：仅项目根目录内读取；支持多引用；限制大小与行数。


### 3.2 Agent（主循环与子代理栈式执行）
**预处理集成**:
- 在 `run()` 开始处调用 `resolve_reference`，将返回的结构化片段拼接到用户消息末尾。

**子代理增强**:
- 处理 `Task` 工具调用时：
  - 整合 `resources` 与 `hints` 至子代理初始化上下文。
  - 生成 `context_summary` 并传递，保持轻量与相关性。
  - Sub-agent 默认 `plan_mode=False`。

### 3.3 Task 工具（参数增强）
**Pydantic 输入模型**:
- `goal: str`（必填）
- `resources: List[str] | None`（选填）
- `hints: str | None`（选填）

**执行行为**:
- 将参数原样传递给主代理 `Agent` 的工具处理逻辑。
- 由主代理负责子代理的实例化与上下文注入。

---

## 4. 关键流程

### 4.1 Smart Extract 注入流程
1. CLI 接收用户输入，包含若干 `@file:...` 引用。
2. Agent 调用 `Session.resolve_reference`。
3. 解析并生成 `<Context>...</Context>` 字符串。
4. 追加到用户消息，进入常规 Think-Act 循环。
5. 若上下文过长，压缩策略自动触发。

### 4.2 子代理创建与上下文传递
1. Main Agent 接收 `Task` 调用（含 `goal`、可选 `resources/hints`）。
2. 生成 `context_summary`，拼接 `resources/hints`。
3. 实例化 Sub-agent（`plan_mode=False`），并注入初始上下文。
4. Sub-agent 执行任务，返回结果。
5. Main Agent 回填 Tool 结果并推进后续任务（若处于计划模式）。

---

## 5. 安全与约束
- 读取文件路径必须为项目根目录子路径。
- 对读取内容进行长度限制与截断提示。
- 多文件注入时，按匹配优先级与路径排序，避免重复。
- 子代理默认不启用计划模式，防止递归膨胀。

---

## 6. 开发计划

### Phase 1：能力落地
1. 在 `core/session.py` 实现 `resolve_reference`（解析、匹配、读取、结构化拼接）。
2. 在 `core/agent.py` 的 `run()` 前置流程集成 Smart Extract。

### Phase 2：工具与代理增强
1. 更新 `tools/agent_tools.py` 的 `Task` 输入模型，增加 `resources/hints`。
2. 更新 `core/agent.py` 子代理创建逻辑，注入线索与摘要。

### Phase 3：测试
1. 单元测试：`resolve_reference`（单/多/无匹配、截断、安全路径）。
2. 集成测试：Agent 预处理注入效果与上下文压缩触发。
3. 工具测试：`Task` 参数传递与子代理初始化上下文验证。

---

## 7. 验收标准
1. 提供 `@file:keyword` 时，能正确定位与读取文件，并以 `<Context>` 结构注入当前消息；超长内容截断并提示。
2. 子代理在创建时，若提供 `resources/hints`，其初始上下文包含这些线索，执行结果可验证其利用了线索（通过日志/输出）。
3. 在多引用与多匹配场景下，注入顺序稳定且无重复；无匹配时有明确提示。
4. 触发上下文压缩时，保留最近交互并生成摘要，整体对话仍可继续。

---

## 8. 兼容性与后续扩展
- 与 v1.2 Shell 能力完全兼容；在@file需要搜索文件的时候，Smart Extract 可调用已存在的搜索工具（如 Glob）并复用读取工具。
- 后续可扩展：模糊搜索与语义检索、基于权限策略的自动过滤、对二进制/大文件的摘要化处理。

