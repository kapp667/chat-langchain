#!/usr/bin/env python3
"""Test Sonnet 4.5 backend configuration."""

import asyncio
from langgraph_sdk import get_client


async def test_sonnet45():
    """Test complex question with Sonnet 4.5."""
    client = get_client(url="http://localhost:2024")

    # Create thread
    thread = await client.threads.create()
    thread_id = thread["thread_id"]

    print(f"📝 Testing Sonnet 4.5 with thread {thread_id}")
    print("=" * 60)

    # Complex question from benchmark
    question = (
        "I want to build a research assistant that: "
        "(1) breaks down complex questions into sub-questions, "
        "(2) searches documentation for each sub-question, "
        "(3) synthesizes findings. How should I structure this?"
    )

    print(f"\n❓ Question: {question}\n")
    print("⏳ Waiting for response (Sonnet 4.5 should respond in ~35-40s)...\n")

    import time
    start = time.time()

    # Run and wait
    result = await client.runs.wait(
        thread_id,
        "chat",
        input={"messages": [{"role": "user", "content": question}]},
    )

    elapsed = time.time() - start

    # Extract response
    messages = result.get("messages", [])
    if messages:
        last_message = messages[-1]
        response = last_message.get("content", "")

        print(f"✅ Response received in {elapsed:.1f}s")
        print(f"📊 Response length: {len(response)} chars")
        print(f"\n📄 Response preview (first 500 chars):")
        print("=" * 60)
        print(response[:500] + "..." if len(response) > 500 else response)
        print("=" * 60)

        # Validate
        if elapsed < 60 and len(response) > 1000:
            print(f"\n🎉 SUCCESS: Sonnet 4.5 is working perfectly!")
            print(f"   - Speed: {elapsed:.1f}s (target: <60s)")
            print(f"   - Quality: {len(response)} chars (target: >1000)")
            return True
        else:
            print(f"\n⚠️  WARNING: Performance below expectations")
            print(f"   - Speed: {elapsed:.1f}s (expected: ~35-40s)")
            print(f"   - Length: {len(response)} chars (expected: >3000)")
            return False
    else:
        print("❌ ERROR: No response received")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_sonnet45())
    exit(0 if success else 1)
