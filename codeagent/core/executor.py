import json
import logging
import inspect
from typing import Dict, Any, List, Optional, get_type_hints
from pydantic import BaseModel
from codeagent.tools.registry import ToolRegistry

# Configure logging
logger = logging.getLogger(__name__)

class ToolExecutor:
    """
    Executes tool calls requested by the LLM.
    Supports both sync and async tools.
    """
    
    @staticmethod
    async def execute(tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute a list of tool calls and return results.
        Now supports async execution.
        
        Returns:
            List of result dictionaries (ready to be converted to ToolMessage).
        """
        results = []
        
        for call in tool_calls:
            call_id = call.get("id")
            func_name = call.get("function", {}).get("name")
            arguments_str = call.get("function", {}).get("arguments", "{}")
            
            try:
                # 1. Get tool function
                func = ToolRegistry.get_tool(func_name)
                if not func:
                    raise ValueError(f"Tool '{func_name}' not found")
                
                # 2. Parse arguments
                try:
                    args_dict = json.loads(arguments_str)
                except json.JSONDecodeError:
                    raise ValueError(f"Invalid JSON arguments: {arguments_str}")
                
                # 3. Convert to Pydantic model if needed
                type_hints = {}
                try:
                    type_hints = get_type_hints(func)
                except Exception:
                    pass

                first_param_type = next((t for n, t in type_hints.items() if n != "return"), None)
                
                # Prepare arguments
                if first_param_type and issubclass(first_param_type, BaseModel):
                    tool_args = first_param_type(**args_dict)
                    call_args = (tool_args,)
                    call_kwargs = {}
                else:
                    call_args = ()
                    call_kwargs = args_dict

                # 4. Execute Function (Async or Sync)
                if inspect.iscoroutinefunction(func):
                    output = await func(*call_args, **call_kwargs)
                else:
                    output = func(*call_args, **call_kwargs)
                
                result_content = str(output)
                
            except Exception as e:
                logger.error(f"Error executing tool {func_name}: {e}")
                result_content = f"Error: {str(e)}"
            
            results.append({
                "tool_call_id": call_id,
                "name": func_name,
                "content": result_content
            })
            
        return results
