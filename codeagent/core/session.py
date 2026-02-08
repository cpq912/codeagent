from typing import List, Optional, TYPE_CHECKING
from codeagent.core.message import Message

if TYPE_CHECKING:
    from codeagent.core.llm import LLMClient

class Session:
    """
    Manages the conversation history and context window.
    """
    def __init__(self, system_prompt: str = "You are a helpful coding assistant."):
        self.system_prompt = system_prompt
        self.history: List[Message] = []
        # Initialize with system prompt
        self.history.append(Message.system(content=system_prompt))
        
        # Context Management
        self.max_tokens = 200000 # Default for high-capacity models (e.g. Claude 3.5 Sonnet)
        self.reserved_output_tokens = 8192
        self.compression_boundary = 0

    @property
    def effective_window(self) -> int:
        return self.max_tokens - self.reserved_output_tokens

    def _estimate_tokens(self, text: str) -> int:
        """Rough estimation of tokens: 1 token ~= 4 chars"""
        if not text:
            return 0
        return len(text) // 4

    def _count_tokens(self) -> int:
        """Count total tokens in history"""
        total = 0
        for msg in self.history:
            content = msg.content or ""
            # If tool_calls exist, they also consume tokens. Rough estimate.
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    # function name + args
                    total += self._estimate_tokens(str(tc))
            
            total += self._estimate_tokens(content)
        return total

    def token_usage_ratio(self) -> float:
        current = self._count_tokens()
        if self.effective_window <= 0:
            return 1.0
        return current / self.effective_window

    def add_message(self, message: Message):
        """Add a message to the history."""
        self.history.append(message)
        
    def get_messages(self) -> List[dict]:
        """Get all messages in OpenAI format."""
        return [msg.to_openai_format() for msg in self.history]
    
    def clear(self):
        """Clear history but keep system prompt."""
        self.history = [Message.system(content=self.system_prompt)]
        self.compression_boundary = 0
    
    async def resolve_reference(self, input_text: str) -> str:
        import re
        from pathlib import Path
        
        if not input_text or "@file:" not in input_text:
            return ""
        
        project_root = Path.cwd().resolve()
        pattern = re.compile(r"@file:([^\s]+)")
        keywords = pattern.findall(input_text)
        if not keywords:
            return ""
        
        files = []
        seen = set()
        for kw in keywords:
            try:
                if "/" in kw or "\\" in kw:
                    base = project_root
                    matches = list(base.glob(kw)) if any(ch in kw for ch in "*?[]") else [base.joinpath(kw)]
                else:
                    matches = list(project_root.rglob(f"*{kw}*"))
                for m in matches:
                    if not m.exists() or not m.is_file():
                        continue
                    rp = m.resolve()
                    try:
                        rp.relative_to(project_root)
                    except Exception:
                        continue
                    pstr = str(rp)
                    if pstr in seen:
                        continue
                    seen.add(pstr)
                    files.append(rp)
            except Exception:
                continue
        
        if not files:
            return "<Context><Warning>No files matched for references.</Warning></Context>"
        
        MAX_FILES = 10
        MAX_LINES = 1000
        MAX_BYTES = 200 * 1024
        
        parts = ["<Context>"]
        for fp in files[:MAX_FILES]:
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
                truncated = False
                if len(text.encode("utf-8")) > MAX_BYTES:
                    truncated = True
                    text = text.encode("utf-8")[:MAX_BYTES].decode("utf-8", errors="ignore")
                lines = text.splitlines()
                if len(lines) > MAX_LINES:
                    truncated = True
                    lines = lines[:MAX_LINES]
                data = "\n".join(lines)
                parts.append(f'<File path="{str(fp.relative_to(project_root)).replace("\\","/")}"><![CDATA[')
                parts.append(data)
                parts.append("]]></File>")
                if truncated:
                    parts.append(f'<Note path="{str(fp.relative_to(project_root)).replace("\\","/")}">Truncated</Note>')
            except Exception:
                parts.append(f'<Error path="{str(fp.relative_to(project_root)).replace("\\","/")}">Read failed</Error>')
        parts.append("</Context>")
        return "\n".join(parts)

    async def compress_context(self, llm_client: "LLMClient"):
        """
        Compress context when usage ratio is high.
        Strategy: Summarize messages between compression_boundary and recent messages.
        """
        # Double check ratio to avoid unnecessary work if called speculatively
        if self.token_usage_ratio() < 0.9:
            return

        # 1. Identify Range
        # Keep system prompt (index 0)
        # Keep recent N messages (e.g. last 10)
        preserve_count = 10
        
        # Calculate start index (after system prompt + previous boundary)
        # Initial boundary is 1 (after system prompt).
        start_index = max(1, self.compression_boundary)
        end_index = max(start_index, len(self.history) - preserve_count)
        
        # If there are not enough messages to compress
        if end_index <= start_index:
            return

        messages_to_summarize = self.history[start_index:end_index]
        if not messages_to_summarize:
            return

        # 2. Generate Summary
        # We need to construct a prompt for the LLM to summarize these messages.
        summary_prompt = "Summarize the following conversation history, focusing on key decisions, tool outputs, and current state. Preserve file paths and critical code snippets."
        
        # Prepare messages for the summarizer LLM
        conversation_text = ""
        for msg in messages_to_summarize:
            role = msg.role
            content = msg.content or "[Tool Call/Output]"
            conversation_text += f"{role}: {content}\n"
            
        summary_request = [
            {"role": "user", "content": f"{summary_prompt}\n\nConversation:\n{conversation_text}"}
        ]
        
        try:
            summary_msg = await llm_client.chat(summary_request)
            summary_content = summary_msg.content
            
            # 3. Replace
            # Create a System message with the summary
            summary_message = Message.system(content=f"<Previous Context Summary>: {summary_content}")
            
            # New history: 
            # history[0:start_index] + [New Summary] + history[end_index:]
            new_history = self.history[:start_index] + [summary_message] + self.history[end_index:]
            self.history = new_history
            
            # Update boundary
            # The new summary is at index `start_index`.
            # The next compression should start after this summary.
            self.compression_boundary = start_index + 1
            
        except Exception as e:
            # Log error but don't crash. In a real system, we might want to log this to trace.log
            print(f"Error compressing context: {e}")

    async def summarize_relevant_context(self) -> str:
        """
        Generate a summary of the current context for a sub-agent.
        For MVP, returns the last 10 messages as text.
        """
        recent_msgs = self.history[-10:]
        summary = "Recent context:\n"
        for msg in recent_msgs:
            role = msg.role
            content = msg.content or "[Tool Call/Output]"
            summary += f"{role}: {content}\n"
        return summary
    
    def inject_context(self, context_summary: str):
        """Inject a context summary from parent agent."""
        # Add as a system message after the main system prompt
        self.history.insert(1, Message.system(content=f"Context from Parent Agent:\n{context_summary}"))
