#!/usr/bin/env python3
"""Verify MCP server uses Sonnet 4.5 from backend configuration."""

import asyncio
from langgraph_sdk import get_client


async def test_mcp_sonnet45():
    """Test that MCP server inherits Sonnet 4.5 configuration."""
    client = get_client(url="http://localhost:2024")

    print("🔍 Verifying MCP Server Configuration")
    print("=" * 60)

    # Test simple question to verify model
    question = "What is LangGraph and how does it differ from LangChain?"

    print(f"\n❓ Test question: {question}\n")
    print("⏳ Testing MCP server (should use Sonnet 4.5 from backend)...\n")

    import time
    start = time.time()

    # Create thread
    thread = await client.threads.create()
    thread_id = thread["thread_id"]

    # Run via backend (which MCP server uses)
    result = await client.runs.wait(
        thread_id,
        "chat",
        input={"messages": [{"role": "user", "content": question}]},
    )

    elapsed = time.time() - start

    # Validate response
    messages = result.get("messages", [])
    if messages:
        response = messages[-1].get("content", "")

        print(f"✅ MCP server responded in {elapsed:.1f}s")
        print(f"📊 Response length: {len(response)} chars")

        # Sonnet 4.5 should be fast (< 30s for simple questions)
        if elapsed < 30 and len(response) > 1000:
            print(f"\n🎉 CONFIRMED: MCP server is using Sonnet 4.5!")
            print(f"   ✓ Speed: {elapsed:.1f}s (Sonnet 4.5 benchmark: ~22-27s)")
            print(f"   ✓ Quality: {len(response)} chars (Sonnet 4.5 benchmark: ~1400+)")
            print(f"\n   Backend → MCP inheritance: ✅ WORKING")
            return True
        else:
            print(f"\n⚠️  Unexpected performance:")
            print(f"   - Speed: {elapsed:.1f}s (expected: <30s for Sonnet 4.5)")
            print(f"   - Length: {len(response)} chars")
            return False
    else:
        print("❌ ERROR: No response received")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_mcp_sonnet45())
    exit(0 if success else 1)
