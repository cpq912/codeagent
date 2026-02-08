import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from codeagent.core.session import Session
from codeagent.core.agent import Agent
from codeagent.core.message import Message
from codeagent.tools.agent_tools import submit_task, TaskArgs


@pytest.mark.asyncio
async def test_resolve_reference_exact_path(tmp_path, monkeypatch):
    core_dir = tmp_path / "core"
    core_dir.mkdir()
    (core_dir / "session.py").write_text("class Session:\n    pass\n", encoding="utf-8")
    (core_dir / "agent.py").write_text("class Agent:\n    pass\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    session = Session()
    ctx = await session.resolve_reference("@file:core/session.py")
    assert "<Context>" in ctx
    assert '<File path="core/session.py">' in ctx
    assert "class Session" in ctx


@pytest.mark.asyncio
async def test_agent_run_appends_context(tmp_path, monkeypatch):
    (tmp_path / "x.txt").write_text("hello\nworld\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    settings = MagicMock()
    settings.openai_api_key = "test"
    settings.openai_base_url = "http://test"
    settings.openai_model = "test"

    agent = Agent(settings)
    agent.llm.chat = AsyncMock(return_value=Message.assistant("OK"))

    inputs = "@file:x.txt please read it"
    chunks = []
    async for c in agent.run(inputs):
        chunks.append(c)

    assert "OK" in "".join(chunks)
    # The user message should include injected Context
    user_msg = agent.session.history[1].content
    assert "<Context>" in user_msg
    assert "x.txt" in user_msg


@pytest.mark.asyncio
async def test_submit_task_injects_resources_hints(monkeypatch):
    import codeagent.core.agent as agent_module
    async def fake_run(self, goal, context_summary=None):
        yield "SUB-AGENT-DONE"
    monkeypatch.setattr(agent_module.Agent, "run", fake_run, raising=True)

    # Stub settings to avoid env dependency
    import codeagent.tools.agent_tools as tools_agent_mod
    fake_settings = MagicMock()
    fake_settings.openai_api_key = "test"
    fake_settings.openai_base_url = "http://test"
    fake_settings.openai_model = "test"
    fake_settings.debug_mode = False
    monkeypatch.setattr(tools_agent_mod, "get_settings", lambda: fake_settings, raising=True)

    args = TaskArgs(
        goal="Do something",
        context_summary="Parent summary",
        resources=["src/a.py", "src/b.py"],
        hints="prefer fast path"
    )
    out = await submit_task(args)
    assert "SUB-AGENT-DONE" in out
