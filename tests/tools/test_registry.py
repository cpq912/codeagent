from pydantic import BaseModel, Field
from codeagent.tools.registry import tool, ToolRegistry

class AddArgs(BaseModel):
    a: int = Field(..., description="First number")
    b: int = Field(..., description="Second number")

@tool
def add_numbers(args: AddArgs):
    """Add two numbers."""
    return args.a + args.b

def test_registry_add():
    func = ToolRegistry.get_tool("add_numbers")
    assert func is not None
    assert func(AddArgs(a=1, b=2)) == 3

def test_schema_generation():
    schemas = ToolRegistry.get_schemas()
    assert len(schemas) >= 1
    
    schema = next(s for s in schemas if s["function"]["name"] == "add_numbers")
    assert schema["function"]["description"] == "Add two numbers."
    assert "a" in schema["function"]["parameters"]["properties"]
    assert "b" in schema["function"]["parameters"]["properties"]
