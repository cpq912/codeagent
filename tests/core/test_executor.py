import json
from codeagent.tools.registry import tool, ToolRegistry
from codeagent.core.executor import ToolExecutor
from pydantic import BaseModel, Field

# Mock Tool
class MockArgs(BaseModel):
    name: str

@tool
def greet_tool(args: MockArgs):
    return f"Hello {args.name}"

def test_executor_success():
    call = {
        "id": "call_1",
        "function": {
            "name": "greet_tool",
            "arguments": json.dumps({"name": "World"})
        }
    }
    
    results = ToolExecutor.execute([call])
    
    assert len(results) == 1
    assert results[0]["tool_call_id"] == "call_1"
    assert results[0]["name"] == "greet_tool"
    assert results[0]["content"] == "Hello World"

def test_executor_not_found():
    call = {
        "id": "call_2",
        "function": {
            "name": "unknown_tool",
            "arguments": "{}"
        }
    }
    
    results = ToolExecutor.execute([call])
    
    assert "Error" in results[0]["content"]
    assert "not found" in results[0]["content"]

def test_executor_invalid_args():
    call = {
        "id": "call_3",
        "function": {
            "name": "greet_tool",
            "arguments": "invalid_json"
        }
    }
    
    results = ToolExecutor.execute([call])
    
    assert "Error" in results[0]["content"]
    assert "Invalid JSON" in results[0]["content"]
