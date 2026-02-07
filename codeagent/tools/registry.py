from typing import Callable, Dict, Any, List, Optional, Type, get_type_hints
from pydantic import BaseModel
import inspect

class ToolRegistry:
    """
    Singleton registry for all available tools.
    """
    _tools: Dict[str, Callable] = {}
    _schemas: List[Dict[str, Any]] = []

    @classmethod
    def register(cls, func: Callable):
        """
        Decorator to register a function as a tool.
        The function must have type hints and a docstring.
        If the first argument is a Pydantic model, it's used for schema generation.
        """
        cls._tools[func.__name__] = func
        cls._schemas.append(cls._generate_schema(func))
        return func

    @classmethod
    def get_tool(cls, name: str) -> Optional[Callable]:
        return cls._tools.get(name)

    @classmethod
    def get_schemas(cls) -> List[Dict[str, Any]]:
        return cls._schemas
    
    @staticmethod
    def _generate_schema(func: Callable) -> Dict[str, Any]:
        """
        Generate OpenAI-compatible function schema from Python function.
        Supports Pydantic models as arguments.
        """
        name = func.__name__
        description = inspect.getdoc(func) or ""
        
        # Check if the function uses a Pydantic model as its single argument
        try:
            type_hints = get_type_hints(func)
        except Exception:
            # Fallback if get_type_hints fails
            type_hints = {}
            
        parameters = {"type": "object", "properties": {}, "required": []}
        
        for param_name, param_type in type_hints.items():
            if param_name == "return":
                continue
            
            try:
                if issubclass(param_type, BaseModel):
                    # Use Pydantic's JSON schema generation
                    model_schema = param_type.model_json_schema()
                    parameters["properties"] = model_schema.get("properties", {})
                    parameters["required"] = model_schema.get("required", [])
                else:
                    # Fallback for simple types (MVP only supports Pydantic models for complex args)
                    pass
            except TypeError:
                # Handle cases where param_type is not a class (e.g. typing.List)
                pass

        return {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters
            }
        }

# Alias for easy usage
tool = ToolRegistry.register
