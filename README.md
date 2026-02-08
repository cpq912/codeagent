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

## 文件
-需求文档v1记录功能需求 
-技术方案设计v1记录技术框架设计 
-detailed_design记录每个模块开发的详细设计


## 已解决问题
-补充一个任务管理的模块 
-主agent可给subagent注入必要的更丰富的上下文 
-增加run shell功能，可以直接执行或者通过llm调用 
-增加上下窗口和压缩 
-支持显示引用某个文档，注入上下文

## 待优化问题

高优先级     
--如果时read file，terminal不要输出全部结果    
--taskupdate的更新目前还是又agent调用      
--怎么知道我已有什么功能，可以怎么联动？可能需要对代码库有了解，生成codemap？    
--代码变更策略：先展示 diff 再应用的交互细节、是否支持回滚、冲突处理规则    
--上下文要避免重复加载     
--代码库的向量化，可考虑用claude context 的mcp       
--增加hook模块提高灵活和规范，比如对上下文组成和工具调用指令，返回内容管理的hook      
--工具权限管理，对于以先删除等操作，需要先确认用户是否同意，或者是否有其他风险。     
--上下文内容优化，比如需要删除哪些，只关注哪些内容，然后利用名称替代长段内容等方法      


低优先级   
--对话内容的持久化存储    
--context.py这个文件好像没作用？      
--task过程中可以人为中断，发起讨论，然后继续     
--tool的输出结构优化，避免一些冗余的信息      
--未来的确需要增加每个模块的测试，这样每次迭代后能保证模块功能完整。最好自动生成。     
--agent主动询问客户的能力     
--什么时候需要创建关键记忆，，比如用户的关键表达？或者是核心内容的疑问阐释？     
--缓存机制？（目前没明确说明）  




## 开发者提示
- 开启调试日志：在 .env 中设置 debug_mode=true，将在 logs/trace.log 中写入请求与响应轨迹
- 计划模式：使用 --plan 或环境变量 CODEAGENT_PLAN_MODE=1 开启
