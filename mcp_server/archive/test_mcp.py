#!/usr/bin/env python3
"""Test script for the LangChain Expert MCP server.

This script directly tests the ask_langchain_expert function to verify
the MCP server can communicate with the LangGraph backend.
"""

import asyncio
import os
from langchain_expert import ask_langchain_expert, check_langchain_expert_status


async def test_status():
    """Test the server status check."""
    print("=" * 80)
    print("TEST 1: Checking LangChain Expert System Status")
    print("=" * 80)

    status = await check_langchain_expert_status()
    print(status)
    print()


async def test_simple_question():
    """Test with a simple question about LangChain."""
    print("=" * 80)
    print("TEST 2: Simple Question about LangChain")
    print("=" * 80)
    print("Question: What is LangChain?")
    print()

    # Use GPT-5 mini (default model)
    answer = await ask_langchain_expert(
        question="What is LangChain?",
        timeout=60
    )

    print("Answer:")
    print(answer)
    print()


async def test_complex_question():
    """Test with a more complex question about LangGraph."""
    print("=" * 80)
    print("TEST 3: Complex Question about LangGraph Checkpoints")
    print("=" * 80)
    print("Question: How do LangGraph checkpoints work and how do I use them with PostgreSQL?")
    print()

    # This should use the multi-agent research system
    answer = await ask_langchain_expert(
        question="How do LangGraph checkpoints work and how do I use them with PostgreSQL?",
        timeout=120
    )

    print("Answer:")
    print(answer)
    print()


async def main():
    """Run all tests."""
    try:
        await test_status()
        await test_simple_question()
        await test_complex_question()

        print("=" * 80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 80)

    except Exception as e:
        print("=" * 80)
        print(f"❌ TEST FAILED: {type(e).__name__}")
        print(f"Error: {str(e)}")
        print("=" * 80)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
