from typing import List
from codeagent.core.message import Message

class Session:
    """
    Manages the conversation history and context window.
    """
    def __init__(self, system_prompt: str = "You are a helpful coding assistant."):
        self.system_prompt = system_prompt
        self.history: List[Message] = []
        # Initialize with system prompt
        self.history.append(Message.system(content=system_prompt))

    def add_message(self, message: Message):
        """Add a message to the history."""
        self.history.append(message)
        
    def get_messages(self) -> List[dict]:
        """Get all messages in OpenAI format."""
        return [msg.to_openai_format() for msg in self.history]
    
    def clear(self):
        """Clear history but keep system prompt."""
        self.history = [Message.system(content=self.system_prompt)]
