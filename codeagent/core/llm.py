from typing import List, Optional, Dict, Any
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import json
import logging
import datetime
from pathlib import Path

from codeagent.config import Settings
from codeagent.core.message import Message

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Wrapper around OpenAI compatible API.
    """
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
        self.model = settings.openai_model
        
        # Setup trace logging if debug mode is on
        self.trace_file = None
        if settings.debug_mode:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            self.trace_file = log_dir / "trace.log"

    def _log_trace(self, event: str, data: Any):
        """Log trace data to file if debug mode is enabled."""
        if not self.trace_file:
            return
            
        try:
            timestamp = datetime.datetime.now().isoformat()
            entry = {
                "timestamp": timestamp,
                "event": event,
                "data": data
            }
            with open(self.trace_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"Failed to write trace log: {e}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def chat(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict]] = None) -> Message:
        """
        Send chat completion request.
        """
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.0  # Deterministic for code generation
            }
            
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"

            # Log Request
            self._log_trace("LLM_REQUEST", {
                "model": self.model,
                "messages": messages[-1] if messages else [], # Only log last message to save space? Or full context?
                # Let's log full messages for full context in debug
                "full_messages_count": len(messages),
                "last_message": messages[-1] if messages else None
            })

            response = await self.client.chat.completions.create(**params)
            
            choice = response.choices[0]
            msg = choice.message
            
            # Log Response
            self._log_trace("LLM_RESPONSE", {
                "content": msg.content,
                "tool_calls": [tc.model_dump() for tc in msg.tool_calls] if msg.tool_calls else None
            })
            
            # Convert OpenAI Message to internal Message model
            return Message.assistant(
                content=msg.content,
                tool_calls=[tc.model_dump() for tc in msg.tool_calls] if msg.tool_calls else None
            )
            
        except Exception as e:
            self._log_trace("LLM_ERROR", str(e))
            raise e
