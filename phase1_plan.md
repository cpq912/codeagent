# 阶段一开发计划：骨架搭建 (Skeleton)

**目标**: 构建项目基础结构，实现配置加载、依赖管理，并跑通一个最小化的 REPL（Read-Eval-Print Loop）循环。
**输入**: 空白项目目录。
**输出**: 可运行的 `python -m codeagent.main`，显示交互式终端，并能读取 `.env` 配置。

---

## 1. 基础环境搭建 (Environment Setup)

### 任务 1.0: 虚拟环境初始化
- **操作**:
  - 创建虚拟环境: `python -m venv .venv`
  - 激活环境: `.\.venv\Scripts\Activate.ps1`
  - **关键约束**: 所有后续的依赖安装和脚本运行，必须在此虚拟环境下进行，确保不污染全局环境。
- **验收标准**: 运行 `Get-Command python` 显示路径指向 `.venv` 目录。

### 任务 1.1: 创建目录结构
- **操作**: 创建以下目录树：
  ```text
  codeagent/
  ├── cli/
  ├── core/
  ├── tools/
  ├── commands/
  └── tests/
  ```
- **验收标准**: 运行 `tree` 或 `ls -R` 能看到完整结构。

### 任务 1.2: 依赖管理
- **操作**: 创建 `requirements.txt`，包含：
  - `openai>=1.0.0` (LLM Client)
  - `prompt_toolkit>=3.0.0` (TUI)
  - `rich>=13.0.0` (Rendering)
  - `pydantic>=2.0.0` (Schema)
  - `pydantic-settings>=2.0.0` (Config)
  - `python-dotenv>=1.0.0` (Env)
  - `pytest` & `pytest-asyncio` (Testing)
- **验收标准**: 运行 `pip install -r requirements.txt` 无报错。

---

## 2. 配置模块开发 (Configuration Module)

### 任务 2.1: 环境变量模板
- **操作**: 创建 `.env.example`，包含 `OPENAI_API_KEY`, `OPENAI_BASE_URL` 等字段。
- **验收标准**: 文件存在且包含必要注释。

### 任务 2.2: 配置加载器 (`config.py`)
- **操作**: 使用 `pydantic-settings` 实现 `Settings` 类。
  - 支持从 `.env` 文件自动加载。
  - 验证 API Key 是否为空。
- **测试用例 (`tests/test_config.py`)**:
  - `test_load_config_from_env`: 模拟环境变量，断言配置加载正确。
  - `test_missing_api_key`: 断言在缺失 Key 时抛出 ValidationError。
- **验收标准**: 单元测试通过。

---

## 3. 终端交互开发 (CLI Skeleton)

### 任务 3.1: 简单的 REPL 循环 (`cli/repl.py`)
- **操作**: 使用 `prompt_toolkit` 实现 `run_repl()` 函数。
  - 显示提示符 `CodeAgent >>`。
  - 接收用户输入并返回字符串。
  - 输入 `exit` 或 `quit` 时退出循环。
- **验收标准**: 手动运行脚本，能正常输入和退出。

### 任务 3.2: 入口文件 (`main.py`)
- **操作**: 创建 `codeagent/main.py`。
  - 初始化配置。
  - 启动 REPL 循环。
  - 捕获 `KeyboardInterrupt` (Ctrl+C) 优雅退出。
- **验收标准**: 运行 `python -m codeagent.main` 成功启动应用。

---

## 4. 阶段验收 (Phase Acceptance)
- [ ] 运行 `pytest`，所有配置相关的测试通过。
- [ ] 运行 `python -m codeagent.main`，看到提示符。
- [ ] 输入任意字符回车，程序不崩溃（仅回显或打印）。
- [ ] 配置 `.env` 后，程序能成功读取 API Key（可打印 log 验证）。
