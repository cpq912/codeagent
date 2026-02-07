from typing import Optional, Literal, Dict, Any, List
from pydantic import BaseModel, Field

RoleType = Literal["system", "user", "assistant", "tool"]

class Message(BaseModel):
    """
    Unified Message model for LLM interaction.
    """
    role: RoleType = Field(..., description="Role of the message sender")
    content: Optional[str] = Field(None, description="Text content of the message")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="List of tool calls if any")
    tool_call_id: Optional[str] = Field(None, description="ID of the tool call this message responds to")
    name: Optional[str] = Field(None, description="Name of the tool that generated this output")

    def to_openai_format(self) -> Dict[str, Any]:
        """
        Convert to OpenAI API compatible dictionary format.
        """
        message_dict = {"role": self.role}
        
        if self.content is not None:
            message_dict["content"] = self.content
            
        if self.tool_calls:
            message_dict["tool_calls"] = self.tool_calls
            
        if self.tool_call_id:
            message_dict["tool_call_id"] = self.tool_call_id
            
        if self.name:
            message_dict["name"] = self.name
            
        return message_dict

    @classmethod
    def system(cls, content: str) -> "Message":
        return cls(role="system", content=content)

    @classmethod
    def user(cls, content: str) -> "Message":
        return cls(role="user", content=content)

    @classmethod
    def assistant(cls, content: Optional[str] = None, tool_calls: Optional[List] = None) -> "Message":
        return cls(role="assistant", content=content, tool_calls=tool_calls)
    
    @classmethod
    def tool(cls, tool_call_id: str, content: str, name: str) -> "Message":
        return cls(role="tool", tool_call_id=tool_call_id, content=content, name=name)
