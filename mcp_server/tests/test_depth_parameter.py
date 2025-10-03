#!/usr/bin/env python3
"""Test depth parameter with prompt engineering using Sonnet 4.5."""

import asyncio
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_expert import _ask_expert_internal


async def test_depth_levels():
    """Test all three depth levels with the same question."""

    # Simple question to test depth variations
    question = "What is LangGraph and how does it differ from LangChain?"

    print("=" * 80)
    print("🧪 Testing Depth Parameter with Sonnet 4.5 + Prompt Engineering")
    print("=" * 80)
    print(f"\n📝 Test Question: {question}\n")

    results = {}

    for depth_level in ["quick", "standard", "deep"]:
        print(f"\n{'─' * 80}")
        print(f"🔍 Testing depth='{depth_level}'")
        print(f"{'─' * 80}\n")

        # Configuration for each depth (matching langchain_expert.py)
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

        config = depth_configs[depth_level]

        # Time the request
        start = time.time()

        try:
            response = await _ask_expert_internal(
                question=question,
                model=None,  # Use backend default (Sonnet 4.5)
                timeout=config["timeout"],
                system_instruction=config["instruction"]
            )

            elapsed = time.time() - start

            # Count paragraphs (rough estimate)
            paragraphs = response.count('\n\n') + 1

            # Store results
            results[depth_level] = {
                "time": elapsed,
                "length": len(response),
                "paragraphs": paragraphs,
                "response": response
            }

            # Print summary
            print(f"✅ Response received in {elapsed:.1f}s")
            print(f"📊 Length: {len(response)} chars")
            print(f"📝 Paragraphs: ~{paragraphs}")
            print(f"\n📄 Response preview (first 300 chars):")
            print("─" * 80)
            print(response[:300] + "..." if len(response) > 300 else response)
            print("─" * 80)

        except Exception as e:
            print(f"❌ Error: {e}")
            results[depth_level] = {"error": str(e)}

    # Summary comparison
    print(f"\n{'=' * 80}")
    print("📊 DEPTH COMPARISON SUMMARY")
    print(f"{'=' * 80}\n")

    print(f"{'Depth':<12} {'Time (s)':<12} {'Length (chars)':<18} {'Paragraphs':<12}")
    print("─" * 80)

    for depth in ["quick", "standard", "deep"]:
        if "error" not in results[depth]:
            r = results[depth]
            print(f"{depth:<12} {r['time']:<12.1f} {r['length']:<18} ~{r['paragraphs']:<12}")
        else:
            print(f"{depth:<12} ERROR: {results[depth]['error']}")

    print("\n" + "=" * 80)

    # Validation
    print("\n🔍 VALIDATION:\n")

    if "error" not in results["quick"]:
        quick_time = results["quick"]["time"]
        quick_len = results["quick"]["length"]

        if quick_time < 35 and quick_len < 2000:
            print("✅ QUICK mode: Fast and concise (as expected)")
        else:
            print(f"⚠️  QUICK mode: Slower or longer than expected ({quick_time:.1f}s, {quick_len} chars)")

    if "error" not in results["standard"]:
        std_time = results["standard"]["time"]
        std_len = results["standard"]["length"]

        if 30 < std_time < 60 and 2000 < std_len < 5000:
            print("✅ STANDARD mode: Balanced depth and speed (as expected)")
        else:
            print(f"⚠️  STANDARD mode: Outside expected range ({std_time:.1f}s, {std_len} chars)")

    if "error" not in results["deep"]:
        deep_time = results["deep"]["time"]
        deep_len = results["deep"]["length"]

        if deep_len > 3000:
            print("✅ DEEP mode: Comprehensive analysis (as expected)")
        else:
            print(f"⚠️  DEEP mode: Shorter than expected ({deep_len} chars)")

    # Expected progression
    if all("error" not in results[d] for d in ["quick", "standard", "deep"]):
        quick_len = results["quick"]["length"]
        std_len = results["standard"]["length"]
        deep_len = results["deep"]["length"]

        if quick_len < std_len < deep_len:
            print("✅ Length progression: quick < standard < deep (CORRECT)")
        else:
            print("⚠️  Length progression: NOT following expected pattern")

    print("\n" + "=" * 80)
    print("✨ Test complete! Review results above to validate prompt engineering.")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_depth_levels())
