# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
markkkkkk: stands for "mark as unsolved issue"

## [Unreleased] - v1.3 (Planned)
## [1.3.0] - 2026-02-09
### Features
- **Smart Context Extractor**: 支持显式 `@file:keyword` 引用，进行 Glob 匹配、自动读取并以结构化片段注入到用户消息，降低初始探索成本
- **Hybrid Task Model 增强**: `Task` 工具新增可选参数 `resources` 和 `hints`；Sub-agent 初始化时注入上述线索以加速定位上下文
### Core Changes
- **Agent**: `run` 流程新增 Smart Extract 预处理步骤，解析并注入解析到的上下文；保持上下文压缩触发逻辑
- **Session**: 新增 `resolve_reference` 方法占位用于解析 `@file` 引用；保留 `compress_context` 与 `summarize_relevant_context` 的扩展点

### Bug Fixes
- **PLAN MODE**: Add a configure option in the cli starting command
- **Shell Executor**: Fix the encoding issue on Windows, and add auto virtual environment support,and add python command execute translation(hardcode, this part has not been perfect solved. markkkkkk) 

## [1.2.0] - 2026-02-09
### Architecture Changes
- **Unified Shell Executor**: Designed `ShellExecutor` to support both internal context gathering and external tool calls.

## [1.1.0] - 2026-02-08
### Architecture Changes (Based on Technical Design Diff)
- **Agent Class**:
    - Added `plan_mode` initialization parameter.
    - Added `TaskManager` instance initialization (draft).
    - Updated `run` method to accept `context_summary` for sub-agent context injection.
    - Added Context Monitor logic (check `token_usage_ratio` > 0.9).
    - Added `UpdateTask` tool handling logic loop.
- **Session Class**:
    - Added `reserved_output_tokens` (default 8192).
    - Added `effective_window` property (`max - reserved`).
    - Added `token_usage_ratio` calculation method.
    - Replaced passive `_compress_context` with async `compress_context` stub.
    - Added `summarize_relevant_context` method stub.
- **New Components**:
    - Defined `TaskManager` class structure with `add_task`, `update_status`, `get_next_task` interfaces.

## [1.0.0] - 2026-02-06
### Added
- **MVP Release**: Initial release of CodeAgent CLI.
- **Core**: Basic `Agent` loop (Think-Act), `LLMClient` (OpenAI compatible), and `Session` management.
- **Tools**: Basic file operations (`read_file`, `write_file`, `list_dir`) and `RunCommand`.
- **CLI**: Basic REPL interface using `prompt_toolkit`.
