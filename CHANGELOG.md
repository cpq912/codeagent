# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - v1.3 (Planned)
### Features
- **ShellExecutor**: Unified shell execution service for internal and external use.
- **Smart Context**: Context extraction using `ShellExecutor` for file search.

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
