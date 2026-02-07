from codeagent.core.session import Session
from codeagent.core.message import Message

def test_session_init():
    session = Session(system_prompt="Custom Prompt")
    assert len(session.history) == 1
    assert session.history[0].role == "system"
    assert session.history[0].content == "Custom Prompt"

def test_add_message():
    session = Session()
    msg = Message.user("Hi")
    session.add_message(msg)
    assert len(session.history) == 2
    assert session.history[1] == msg

def test_get_messages_format():
    session = Session()
    session.add_message(Message.user("Hi"))
    formatted = session.get_messages()
    assert len(formatted) == 2
    assert formatted[1] == {"role": "user", "content": "Hi"}

def test_clear_session():
    session = Session()
    session.add_message(Message.user("Hi"))
    session.clear()
    assert len(session.history) == 1
    assert session.history[0].role == "system"
