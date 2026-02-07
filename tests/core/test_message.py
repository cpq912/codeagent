from codeagent.core.message import Message

def test_user_message():
    msg = Message.user("Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"
    assert msg.to_openai_format() == {"role": "user", "content": "Hello"}

def test_system_message():
    msg = Message.system("System prompt")
    assert msg.role == "system"
    assert msg.content == "System prompt"

def test_assistant_message():
    msg = Message.assistant("I am AI")
    assert msg.role == "assistant"
    assert msg.content == "I am AI"

def test_tool_calls_message():
    tool_calls = [{"id": "call_1", "type": "function", "function": {"name": "test"}}]
    msg = Message.assistant(content=None, tool_calls=tool_calls)
    assert msg.tool_calls == tool_calls
    assert msg.content is None
    assert "tool_calls" in msg.to_openai_format()

def test_tool_result_message():
    msg = Message.tool(tool_call_id="call_1", content="result", name="read_file")
    assert msg.role == "tool"
    assert msg.tool_call_id == "call_1"
    assert msg.name == "read_file"
    assert msg.to_openai_format() == {
        "role": "tool",
        "tool_call_id": "call_1",
        "content": "result",
        "name": "read_file"
    }
