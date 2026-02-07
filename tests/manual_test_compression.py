import asyncio
from unittest.mock import MagicMock, AsyncMock
from codeagent.core.session import Session
from codeagent.core.message import Message
from codeagent.core.llm import LLMClient

async def run_test():
    print("=== Context Compression Test ===\n")

    # 1. Setup Session with small limits
    session = Session(system_prompt="System Prompt")
    session.max_tokens = 1000
    session.reserved_output_tokens = 200
    effective = session.effective_window # 800
    print(f"Config: Max={session.max_tokens}, Reserved={session.reserved_output_tokens}, Effective={effective}")
    print(f"Compression Threshold: 90% ({effective * 0.9} tokens)\n")

    # 2. Mock LLM Client
    mock_llm = AsyncMock(spec=LLMClient)
    # Mock the chat method to return a summary
    mock_summary_response = Message.assistant(content="[SUMMARY: Old conversation summarized here...]")
    mock_llm.chat.return_value = mock_summary_response

    # 3. Fill Context
    # We use estimate: 1 token ~= 4 chars.
    # To reach > 720 tokens, we need > 2880 chars.
    # Let's add messages of ~50 tokens (200 chars) each, so we can add more messages (>10).
    
    msg_content = "A" * 200 # ~50 tokens
    
    print("--- Filling Context ---")
    for i in range(1, 30): # Increase loop to ensure we pass preserve_count (10)
        session.add_message(Message.user(content=f"Msg {i}: {msg_content}"))
        current_tokens = session._count_tokens()
        ratio = session.token_usage_ratio()
        print(f"Added Msg {i}. Total Tokens: {current_tokens}. Ratio: {ratio:.2%}")
        
        # Check compression
        if ratio > 0.9:
            print("\n>>> Threshold exceeded! Triggering compression...")
            await session.compress_context(mock_llm)
            
            # Print status after compression
            new_tokens = session._count_tokens()
            new_ratio = session.token_usage_ratio()
            print(f">>> Compression Done.")
            print(f"New Total Tokens: {new_tokens}. New Ratio: {new_ratio:.2%}")
            
            # Inspect History
            print("\n--- History Inspection ---")
            for idx, msg in enumerate(session.history):
                role = msg.role
                content_preview = msg.content[:50] + "..." if msg.content else "None"
                print(f"[{idx}] {role}: {content_preview}")
            break

if __name__ == "__main__":
    asyncio.run(run_test())
