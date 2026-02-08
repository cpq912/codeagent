# CodeAgent CLI

一个在本地运行的代码智能代理，支持工具调用、上下文注入与计划模式。

## 环境要求
- Windows 或 Linux/Mac（推荐 Windows）
- Python 3.10+（推荐 3.11+）
- 具备可访问 OpenAI 兼容服务的 API Key

## 安装步骤
1. 克隆或下载本仓库到本地
2. 创建并激活虚拟环境（Windows 示例）
   - python -m venv .venv
   - .\.venv\Scripts\python -m pip install --upgrade pip
3. 安装依赖
   - .\.venv\Scripts\python -m pip install -r requirements.txt
4. 配置 .env
   - 在项目根目录创建 .env，包含：
     - openai_api_key=你的APIKey
     - openai_base_url=你的OpenAI兼容服务地址
     - openai_model=模型名称（默认 qwen-plus，可按需更改）

## 启动 CLI
- 直接启动（推荐使用虚拟环境）
  - .\.venv\Scripts\python -m codeagent.main
- 开启计划模式
  - .\.venv\Scripts\python -m codeagent.main --plan

## 使用说明
- 进入 CLI 后输入你的指令并回车
- 支持引用文件上下文：在输入中添加 @file:关键词 或相对路径，自动注入文件片段
- 支持工具调用：例如读取文件、搜索、运行 Shell 命令等，工具输出会显示在面板中
- 退出：输入 exit 或 quit

## 常见问题
- 中文输出乱码：已在 Shell 执行器中统一为 UTF-8；如仍出现问题，请确认终端编码设置
- 运行 Python 脚本报找不到包：在子目录运行脚本时，执行器已注入 PYTHONPATH=项目根目录确保能导入本地包

## 开发者提示
- 开启调试日志：在 .env 中设置 debug_mode=true，将在 logs/trace.log 中写入请求与响应轨迹
- 计划模式：使用 --plan 或环境变量 CODEAGENT_PLAN_MODE=1 开启
