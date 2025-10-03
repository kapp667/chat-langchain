#!/usr/bin/env python3
"""Test depth parameter by calling backend API directly with system instructions."""

import asyncio
import time
from langgraph_sdk import get_client


async def test_depth_with_system_instruction(
    question: str,
    depth_name: str,
    system_instruction: str,
    timeout: int
):
    """Test a specific depth level."""

    client = get_client(url="http://localhost:2024")

    # Create thread
    thread = await client.threads.create()
    thread_id = thread["thread_id"]

    # Prepare messages with system instruction
    messages = [
        {"role": "system", "content": system_instruction},
        {"role": "user", "content": question}
    ]

    # Time the request
    start = time.time()

    try:
        # Run with backend default model (Sonnet 4.5)
        result = await asyncio.wait_for(
            client.runs.wait(
                thread_id,
                "chat",
                input={"messages": messages}
            ),
            timeout=timeout
        )

        elapsed = time.time() - start

        # Extract response
        response_messages = result.get("messages", [])
        response = ""
        if response_messages:
            for msg in reversed(response_messages):
                if isinstance(msg, dict) and msg.get("type") == "ai":
                    response = msg.get("content", "")
                    break

        # Count paragraphs (rough estimate)
        paragraphs = response.count('\n\n') + 1

        return {
            "depth": depth_name,
            "time": elapsed,
            "length": len(response),
            "paragraphs": paragraphs,
            "response": response,
            "success": True
        }

    except asyncio.TimeoutError:
        elapsed = time.time() - start
        return {
            "depth": depth_name,
            "time": elapsed,
            "success": False,
            "error": f"Timeout after {timeout}s"
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "depth": depth_name,
            "time": elapsed,
            "success": False,
            "error": str(e)
        }


async def main():
    """Run depth parameter tests."""

    question = "What is LangGraph and how does it differ from LangChain?"

    print("=" * 80)
    print("🧪 Testing Depth Parameter with Sonnet 4.5 + Prompt Engineering")
    print("=" * 80)
    print(f"\n📝 Test Question: {question}\n")

    # Define depth configurations (matching langchain_expert.py)
    depth_configs = {
        "quick": {
            "timeout": 90,
            "instruction": """You are providing a QUICK, CONCISE answer optimized for speed.

CONSTRAINTS:
• Maximum 2-3 paragraphs total
• Focus on essential information only
• Skip detailed explanations unless critical
• Provide 1-2 code examples maximum (only if directly answering the question)
• Brief citations (just source names, no URLs needed)

STYLE:
• Direct and to-the-point
• No preamble or lengthy introductions
• Answer the core question immediately

Remember: The user needs a fast answer. Prioritize clarity over completeness."""
        },
        "standard": {
            "timeout": 120,
            "instruction": """You are providing a DETAILED, BALANCED answer with comprehensive coverage.

GUIDELINES:
• Provide 4-6 well-structured paragraphs
• Include multiple code examples (2-4) showing different approaches
• Explain both the 'how' and 'why' behind recommendations
• Cover edge cases and common pitfalls
• Include citations with source references

STRUCTURE:
• Start with a clear, direct answer to the question
• Follow with implementation details and code examples
• End with best practices or additional considerations

STYLE:
• Professional and thorough
• Balance depth with readability
• Assume intermediate-level familiarity with LangChain concepts

Remember: This is the default mode - aim for production-ready guidance."""
        },
        "deep": {
            "timeout": 240,
            "instruction": """You are providing an IN-DEPTH, EXHAUSTIVE analysis with maximum thoroughness.

EXPECTATIONS:
• Comprehensive, production-grade explanation (6-10+ paragraphs)
• Multiple detailed code examples (4-8) covering:
  - Basic implementation
  - Advanced patterns
  - Error handling
  - Performance optimization
  - Real-world production scenarios
• Architectural considerations and design patterns
• Complete coverage of edge cases, limitations, and trade-offs
• Detailed citations with specific source references

STRUCTURE:
• Executive summary: Direct answer with key takeaways
• Core implementation: Step-by-step with code
• Advanced topics: Optimization, scaling, error handling
• Architecture: Design patterns, best practices, anti-patterns
• Complete working examples when applicable

STYLE:
• Expert-level depth and precision
• Assume the user needs production-ready, battle-tested guidance
• Include context about when to use vs. not use certain approaches
• Reference related LangChain/LangGraph concepts for completeness

Remember: This is for complex, critical questions where the user needs comprehensive mastery of the topic."""
        }
    }

    results = {}

    for depth_name, config in depth_configs.items():
        print(f"\n{'─' * 80}")
        print(f"🔍 Testing depth='{depth_name}'")
        print(f"{'─' * 80}\n")

        result = await test_depth_with_system_instruction(
            question=question,
            depth_name=depth_name,
            system_instruction=config["instruction"],
            timeout=config["timeout"]
        )

        results[depth_name] = result

        if result["success"]:
            print(f"✅ Response received in {result['time']:.1f}s")
            print(f"📊 Length: {result['length']} chars")
            print(f"📝 Paragraphs: ~{result['paragraphs']}")
            print(f"\n📄 Response preview (first 300 chars):")
            print("─" * 80)
            preview = result['response'][:300] + "..." if len(result['response']) > 300 else result['response']
            print(preview)
            print("─" * 80)
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")

    # Summary
    print(f"\n{'=' * 80}")
    print("📊 DEPTH COMPARISON SUMMARY")
    print(f"{'=' * 80}\n")

    print(f"{'Depth':<12} {'Time (s)':<12} {'Length (chars)':<18} {'Paragraphs':<12} {'Status'}")
    print("─" * 80)

    for depth_name in ["quick", "standard", "deep"]:
        r = results[depth_name]
        if r["success"]:
            print(f"{depth_name:<12} {r['time']:<12.1f} {r['length']:<18} ~{r['paragraphs']:<12} ✅")
        else:
            print(f"{depth_name:<12} {r['time']:<12.1f} {'N/A':<18} {'N/A':<12} ❌ {r['error']}")

    print("\n" + "=" * 80)

    # Validation
    print("\n🔍 VALIDATION:\n")

    all_success = all(r["success"] for r in results.values())

    if all_success:
        quick_len = results["quick"]["length"]
        std_len = results["standard"]["length"]
        deep_len = results["deep"]["length"]

        # Check progression
        if quick_len < std_len < deep_len:
            print("✅ Length progression: quick < standard < deep (CORRECT)")
        else:
            print(f"⚠️  Length progression: quick={quick_len}, standard={std_len}, deep={deep_len}")

        # Check quick mode
        if results["quick"]["time"] < 35 and quick_len < 2000:
            print("✅ QUICK mode: Fast and concise (as expected)")
        else:
            print(f"⚠️  QUICK mode: {results['quick']['time']:.1f}s, {quick_len} chars")

        # Check standard mode
        if 30 < results["standard"]["time"] < 60 and 2000 < std_len < 5000:
            print("✅ STANDARD mode: Balanced (as expected)")
        else:
            print(f"⚠️  STANDARD mode: {results['standard']['time']:.1f}s, {std_len} chars")

        # Check deep mode
        if deep_len > 3000:
            print("✅ DEEP mode: Comprehensive (as expected)")
        else:
            print(f"⚠️  DEEP mode: {deep_len} chars (expected >3000)")
    else:
        print("❌ Some tests failed - check errors above")

    print("\n" + "=" * 80)
    print("✨ Test complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
