#!/usr/bin/env python3
"""MCP Server for LangChain/LangGraph Expert Chat.

This MCP server provides access to a sophisticated LangChain documentation expert
powered by a self-hosted LangGraph application with RAG over 15,061+ documents.

The server exposes a tool that Claude Code can use to ask questions about:
- LangChain concepts, APIs, and best practices
- LangGraph workflows, state management, and deployment
- Integration patterns and architecture decisions
- Troubleshooting and debugging guidance
"""

import asyncio
import os
from typing import Literal, Optional
from uuid import uuid4

from langgraph_sdk import get_client
from mcp.server.fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP(
    "LangChain Expert",
    dependencies=["langgraph-sdk>=0.1.28"]
)

# LangGraph server configuration
LANGGRAPH_URL = os.getenv("LANGGRAPH_URL", "http://localhost:2024")
ASSISTANT_ID = "chat"  # From langgraph.json

# Session management (simple in-memory cache)
_thread_cache: dict[str, str] = {}


async def _get_or_create_thread_id(session_id: Optional[str] = None) -> str:
    """Get existing thread ID or create a new one.

    Args:
        session_id: Optional session identifier for thread reuse

    Returns:
        Thread ID from LangGraph server
    """
    if session_id and session_id in _thread_cache:
        return _thread_cache[session_id]

    # Create new thread via LangGraph API
    client = get_client(url=LANGGRAPH_URL)
    thread = await client.threads.create()
    thread_id = thread["thread_id"]

    if session_id:
        _thread_cache[session_id] = thread_id

    return thread_id


async def _ask_expert_internal(
    question: str,
    model: str,
    timeout: int,
    session_id: Optional[str] = None
) -> str:
    """Internal function for querying the LangChain expert system.

    This function contains the core logic for all expert queries,
    used by the public-facing tools with different configurations.

    Args:
        question: Question to ask
        model: OpenAI/Anthropic model identifier
        timeout: Maximum seconds to wait for response
        session_id: Optional session ID for conversation context

    Returns:
        Expert answer with citations
    """
    try:
        # Get or create thread (this also initializes client)
        thread_id = await _get_or_create_thread_id(session_id)

        # Initialize LangGraph SDK client
        client = get_client(url=LANGGRAPH_URL)

        # Prepare input
        input_data = {
            "messages": [
                {
                    "role": "user",
                    "content": question
                }
            ]
        }

        # Configure models
        config = {
            "configurable": {
                "query_model": model,
                "response_model": model
            }
        }

        # Stream response from LangGraph
        response_text = ""
        last_messages = []

        # Set timeout
        async def run_with_timeout():
            nonlocal response_text, last_messages

            async for chunk in client.runs.stream(
                thread_id,
                ASSISTANT_ID,
                input=input_data,
                config=config,
                stream_mode="messages"
            ):
                # Extract final messages
                if hasattr(chunk, "data") and chunk.data:
                    # Check if it's a message update
                    if isinstance(chunk.data, list):
                        last_messages = chunk.data
                    elif isinstance(chunk.data, dict) and "messages" in chunk.data:
                        last_messages = chunk.data["messages"]

        # Execute with timeout
        try:
            await asyncio.wait_for(run_with_timeout(), timeout=timeout)
        except asyncio.TimeoutError:
            return f"⏱️ Request timed out after {timeout} seconds. The question may be too complex. Try:\n1. Breaking it into simpler questions\n2. Using a longer timeout\n3. Checking if langgraph dev is running (http://localhost:2024)"

        # Extract final response
        if last_messages:
            # Get the last AI message
            for msg in reversed(last_messages):
                if isinstance(msg, dict):
                    # Handle dict format
                    if msg.get("type") == "ai" or msg.get("role") == "assistant":
                        response_text = msg.get("content", "")
                        break
                elif hasattr(msg, "type") and msg.type == "ai":
                    # Handle message object format
                    response_text = msg.content
                    break

        if not response_text:
            return "⚠️ No response received. The system may be processing. Try:\n1. Checking if langgraph dev is running: curl http://localhost:2024/health\n2. Viewing logs: tail -50 /tmp/langgraph_dev.log\n3. Simplifying your question"

        return response_text

    except ConnectionError as e:
        return f"❌ Connection error: Cannot reach LangGraph server at {LANGGRAPH_URL}\n\nPlease ensure 'langgraph dev' is running:\n  cd /Users/stephane/Documents/work/chat-langchain\n  langgraph dev\n\nError details: {str(e)}"

    except Exception as e:
        return f"❌ Unexpected error: {type(e).__name__}: {str(e)}\n\nThis may indicate:\n1. LangGraph server is not running\n2. Invalid model name (check supported models)\n3. System resource issues\n\nTry checking the logs: tail -50 /tmp/langgraph_dev.log"


@mcp.tool()
async def ask_langchain_expert(
    question: str,
    depth: Literal["quick", "standard", "deep"] = "standard",
    session_id: Optional[str] = None
) -> str:
    """Ask the LangChain/LangGraph documentation expert with configurable response depth.

    This tool queries a sophisticated RAG system with:
    - 15,061+ indexed documents from LangChain/LangGraph documentation
    - Multi-agent research planning for complex queries
    - Citation-backed responses with source references
    - Configurable intelligence levels optimized for speed vs depth

    Choose the right depth based on your question complexity:

    Args:
        question: Your question about LangChain, LangGraph, or related topics.
                 Be specific for best results.

        depth: Response depth level (choose based on question complexity):

            🏃 "quick" - Ultra-fast answers with GPT-4o-mini (~5-10 seconds)
               Best for:
               • Simple factual questions ("What is a Runnable?")
               • Quick API lookups ("How to use ChatOpenAI?")
               • Basic concept explanations
               • When speed is critical

            ⚖️ "standard" - Balanced answers with GPT-5 mini (~10-20 seconds) [DEFAULT]
               Best for:
               • Most questions (80% of use cases)
               • Detailed explanations with code examples
               • Troubleshooting guidance
               • Best practices questions
               • Integration patterns

            🧠 "deep" - Maximum reasoning with GPT-5 full (~60-180 seconds)
               ⚠️ WARNING: Maximum 4 minutes due to Claude Desktop timeout
               If your question times out, try:
               • Breaking it into smaller, focused questions
               • Using "standard" mode first for research, then "deep" for synthesis

               Best for:
               • Complex architecture design (focused questions)
               • Multi-step reasoning problems
               • In-depth technical analysis
               • Performance optimization strategies
               • Advanced debugging scenarios

        session_id: Optional session ID to maintain conversation context.
                   Use the same ID for follow-up questions to preserve context.

    Returns:
        Detailed answer with citations from LangChain documentation.

    Examples:
        # Quick factual question
        ask_langchain_expert("What is LCEL?", depth="quick")

        # Standard detailed question (most common)
        ask_langchain_expert("How do I implement streaming in LangChain?")

        # Complex architecture question
        ask_langchain_expert(
            "Design a multi-agent system with human-in-the-loop and checkpoints",
            depth="deep"
        )

        # Follow-up questions in same session
        ask_langchain_expert("Explain LangGraph checkpoints", session_id="learning")
        ask_langchain_expert("How to use PostgreSQL saver?", session_id="learning")
    """
    # Configuration map for different depth levels
    depth_config = {
        "quick": {
            "model": "openai/gpt-4o-mini",
            "timeout": 60
        },
        "standard": {
            "model": "openai/gpt-5-mini-2025-08-07",
            "timeout": 120
        },
        "deep": {
            "model": "openai/gpt-5-2025-08-07",
            "timeout": 240  # 4 minutes (Claude Desktop client limit)
        }
    }

    config = depth_config[depth]

    # Call internal implementation
    return await _ask_expert_internal(
        question=question,
        model=config["model"],
        timeout=config["timeout"],
        session_id=session_id
    )


@mcp.tool()
def clear_session(session_id: str) -> str:
    """Clear a conversation session to start fresh.

    Use this when you want to change topics or reset the conversation context.
    This is a normal usage feature for managing conversation state.

    Args:
        session_id: Session ID to clear

    Returns:
        Confirmation message
    """
    if session_id in _thread_cache:
        del _thread_cache[session_id]
        return f"✅ Session '{session_id}' cleared. Next question will start a new conversation."
    else:
        return f"ℹ️ Session '{session_id}' not found (may have already been cleared or never existed)."


@mcp.tool()
def list_sessions() -> str:
    """[DEBUG] List all active conversation sessions.

    Use this only for debugging or inspecting system state.

    Returns:
        List of active session IDs
    """
    if not _thread_cache:
        return "No active sessions."

    sessions = "\n".join(f"- {sid} (thread: {tid[:8]}...)" for sid, tid in _thread_cache.items())
    return f"Active sessions ({len(_thread_cache)}):\n{sessions}"


@mcp.tool()
async def check_langchain_expert_status() -> str:
    """[MONITORING] Check if the LangChain expert system is operational.

    Use this for health checks and troubleshooting connectivity issues.

    Returns:
        Status message with system information
    """
    try:
        client = get_client(url=LANGGRAPH_URL)

        # Try to list assistants to verify connection
        try:
            assistants = await client.assistants.search()
            assistant_names = [a.get("assistant_id", "unknown") for a in assistants] if assistants else []

            return f"""✅ LangChain Expert System: OPERATIONAL

Server: {LANGGRAPH_URL}
Available Assistants: {', '.join(assistant_names) if assistant_names else 'chat'}
Active Sessions: {len(_thread_cache)}
Indexed Documents: 15,061+ (LangChain/LangGraph documentation)

Intelligence Levels Available:
🏃 quick   - GPT-4o-mini (~5-10s)        - Simple questions, fast lookups
⚖️ standard - GPT-5 mini (~10-20s)       - Most questions (default)
🧠 deep     - GPT-5 full (~60-120s)      - Complex architecture, deep reasoning

Ready to answer questions about LangChain and LangGraph!"""

        except Exception as e:
            return f"⚠️ Connected to {LANGGRAPH_URL} but cannot verify assistants: {str(e)}\n\nThe server may still be functional. Try asking a question."

    except Exception as e:
        return f"""❌ LangChain Expert System: NOT AVAILABLE

Server: {LANGGRAPH_URL}
Error: {type(e).__name__}: {str(e)}

Please ensure 'langgraph dev' is running:
  cd /Users/stephane/Documents/work/chat-langchain
  langgraph dev

Check logs: tail -50 /tmp/langgraph_dev.log"""


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
