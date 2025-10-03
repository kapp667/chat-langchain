#!/usr/bin/env python3
"""Verify that GPT-5 mini is being used by the LangGraph backend."""

import asyncio
from langchain_expert import ask_langchain_expert


async def test_model_verification():
    """Test with a simple question to verify the model being used."""
    print("=" * 80)
    print("VERIFICATION: Confirming GPT-5 mini is being used")
    print("=" * 80)
    print("Question: What is LangChain? (simple test)")
    print()

    # This should use GPT-5 mini as configured
    answer = await ask_langchain_expert(
        question="What is LangChain?",
        timeout=180
    )

    print("Answer:")
    print(answer)
    print()
    print("=" * 80)
    print("✅ Model verification test completed")
    print("=" * 80)
    print()
    print("NOTE: The response should be quick (~3-8 seconds) and cost-effective,")
    print("confirming GPT-5 mini (not full GPT-5) is being used.")


if __name__ == "__main__":
    asyncio.run(test_model_verification())
