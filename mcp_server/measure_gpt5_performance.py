#!/usr/bin/env python3
"""Script to empirically measure GPT-5 response times for deep mode evaluation.

This script tests the actual chat-langchain system with GPT-5 to determine:
1. Real-world response times for questions of varying complexity
2. Whether GPT-5 is suitable for deep mode (must be <240s)
3. Whether we need to switch to a faster model (Claude Sonnet 4.5, GPT-4o)

Usage:
    cd /Users/stephane/Documents/work/chat-langchain
    python mcp_server/measure_gpt5_performance.py
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List

from langgraph_sdk import get_client

# Configuration
LANGGRAPH_URL = "http://localhost:2024"
ASSISTANT_ID = "chat"
MODEL = "openai/gpt-5-2025-08-07"  # GPT-5 full (current deep mode config)

# Test questions with increasing complexity
TEST_QUESTIONS = [
    {
        "id": "test_1_simple",
        "question": "What is LangGraph and how does it differ from LangChain?",
        "complexity": "simple",
        "expected_time": "30-60s",
        "description": "Simple factual question with basic comparison"
    },
    {
        "id": "test_2_moderate",
        "question": "Explain how LangGraph checkpoints work with PostgreSQL, including the AsyncPostgresSaver class and how to handle migration between checkpoint versions.",
        "complexity": "moderate",
        "expected_time": "60-120s",
        "description": "Detailed technical question requiring multiple doc sections"
    },
    {
        "id": "test_3_complex",
        "question": "Design a production-grade multi-agent LangGraph system with the following requirements: (1) human-in-the-loop approval for critical decisions, (2) PostgreSQL checkpoints for state persistence, (3) error recovery and retry logic, (4) observability with LangSmith, and (5) deployment strategy. Provide architectural decisions and code examples.",
        "complexity": "complex",
        "expected_time": "120-240s",
        "description": "Multi-step architecture question requiring deep reasoning"
    }
]


async def run_single_test(test_config: Dict) -> Dict:
    """Run a single test and measure response time.

    Args:
        test_config: Test configuration with question and metadata

    Returns:
        Dictionary with test results including timing and response
    """
    print(f"\n{'='*80}")
    print(f"Test: {test_config['id']}")
    print(f"Complexity: {test_config['complexity']}")
    print(f"Expected: {test_config['expected_time']}")
    print(f"Question: {test_config['question'][:100]}...")
    print(f"{'='*80}\n")

    try:
        # Initialize client
        client = get_client(url=LANGGRAPH_URL)

        # Create thread
        thread = await client.threads.create()
        thread_id = thread["thread_id"]

        # Prepare input
        input_data = {
            "messages": [
                {
                    "role": "user",
                    "content": test_config["question"]
                }
            ]
        }

        # Configure GPT-5
        config = {
            "configurable": {
                "query_model": MODEL,
                "response_model": MODEL
            }
        }

        # Start timing
        start_time = time.time()
        start_datetime = datetime.now().isoformat()

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting request...")

        # Stream response
        response_text = ""
        last_messages = []
        chunk_count = 0

        async for chunk in client.runs.stream(
            thread_id,
            ASSISTANT_ID,
            input=input_data,
            config=config,
            stream_mode="messages"
        ):
            chunk_count += 1

            # Print progress every 10 chunks
            if chunk_count % 10 == 0:
                elapsed = time.time() - start_time
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Processing... ({elapsed:.1f}s elapsed, {chunk_count} chunks)")

            # Extract messages
            if hasattr(chunk, "data") and chunk.data:
                if isinstance(chunk.data, list):
                    last_messages = chunk.data
                elif isinstance(chunk.data, dict) and "messages" in chunk.data:
                    last_messages = chunk.data["messages"]

        # End timing
        end_time = time.time()
        end_datetime = datetime.now().isoformat()
        elapsed_time = end_time - start_time

        # Extract final response
        if last_messages:
            for msg in reversed(last_messages):
                if isinstance(msg, dict):
                    if msg.get("type") == "ai" or msg.get("role") == "assistant":
                        response_text = msg.get("content", "")
                        break
                elif hasattr(msg, "type") and msg.type == "ai":
                    response_text = msg.content
                    break

        # Print results
        print(f"\n{'─'*80}")
        print(f"✅ Test completed successfully")
        print(f"⏱️  Time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
        print(f"📊 Chunks received: {chunk_count}")
        print(f"📝 Response length: {len(response_text)} characters")
        print(f"{'─'*80}")

        # Evaluate vs 240s limit
        within_limit = elapsed_time < 240
        status_emoji = "✅" if within_limit else "⚠️"
        status_text = "PASS (within 4min limit)" if within_limit else "FAIL (exceeds 4min limit)"

        print(f"\n{status_emoji} Status: {status_text}")
        if not within_limit:
            print(f"⚠️  Exceeded limit by: {elapsed_time - 240:.2f} seconds")

        return {
            "test_id": test_config["id"],
            "complexity": test_config["complexity"],
            "success": True,
            "elapsed_time": elapsed_time,
            "elapsed_minutes": elapsed_time / 60,
            "within_limit": within_limit,
            "chunk_count": chunk_count,
            "response_length": len(response_text),
            "start_time": start_datetime,
            "end_time": end_datetime,
            "response_preview": response_text[:200] + "..." if len(response_text) > 200 else response_text
        }

    except Exception as e:
        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f"\n{'─'*80}")
        print(f"❌ Test failed")
        print(f"⏱️  Time before failure: {elapsed_time:.2f} seconds")
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        print(f"{'─'*80}")

        return {
            "test_id": test_config["id"],
            "complexity": test_config["complexity"],
            "success": False,
            "elapsed_time": elapsed_time,
            "elapsed_minutes": elapsed_time / 60,
            "within_limit": False,
            "error": f"{type(e).__name__}: {str(e)}"
        }


async def run_all_tests() -> List[Dict]:
    """Run all performance tests sequentially.

    Returns:
        List of test results
    """
    print("\n" + "="*80)
    print("GPT-5 Performance Measurement for Deep Mode")
    print("="*80)
    print(f"\nModel: {MODEL}")
    print(f"Target: <240 seconds (4 minutes)")
    print(f"Tests: {len(TEST_QUESTIONS)}")
    print(f"LangGraph URL: {LANGGRAPH_URL}")

    # Verify LangGraph is running
    try:
        client = get_client(url=LANGGRAPH_URL)
        assistants = await client.assistants.search()
        print(f"✅ LangGraph server operational ({len(assistants)} assistants)")
    except Exception as e:
        print(f"\n❌ ERROR: Cannot connect to LangGraph server at {LANGGRAPH_URL}")
        print(f"Please ensure 'langgraph dev' is running:")
        print(f"  cd /Users/stephane/Documents/work/chat-langchain")
        print(f"  langgraph dev")
        return []

    results = []

    for i, test_config in enumerate(TEST_QUESTIONS, 1):
        print(f"\n\n{'#'*80}")
        print(f"# Test {i}/{len(TEST_QUESTIONS)}: {test_config['complexity'].upper()}")
        print(f"{'#'*80}")

        result = await run_single_test(test_config)
        results.append(result)

        # Wait between tests to avoid rate limits
        if i < len(TEST_QUESTIONS):
            print(f"\n⏸️  Waiting 5 seconds before next test...")
            await asyncio.sleep(5)

    return results


def print_summary(results: List[Dict]):
    """Print summary of all test results.

    Args:
        results: List of test results
    """
    print("\n\n" + "="*80)
    print("SUMMARY: GPT-5 Performance Test Results")
    print("="*80)

    if not results:
        print("\n❌ No results to display")
        return

    # Statistics
    successful_tests = [r for r in results if r.get("success", False)]
    failed_tests = [r for r in results if not r.get("success", False)]
    within_limit = [r for r in successful_tests if r.get("within_limit", False)]

    print(f"\nTests completed: {len(results)}")
    print(f"✅ Successful: {len(successful_tests)}")
    print(f"❌ Failed: {len(failed_tests)}")
    print(f"✅ Within 4min limit: {len(within_limit)}/{len(successful_tests)}")

    # Detailed results
    print("\n" + "-"*80)
    print("Detailed Results:")
    print("-"*80)

    for result in results:
        status = "✅ PASS" if result.get("success") and result.get("within_limit") else "❌ FAIL"

        print(f"\n{result['test_id']} ({result['complexity']}):")
        print(f"  Status: {status}")
        print(f"  Time: {result['elapsed_time']:.2f}s ({result['elapsed_minutes']:.2f}min)")

        if result.get("success"):
            print(f"  Chunks: {result.get('chunk_count', 'N/A')}")
            print(f"  Response length: {result.get('response_length', 'N/A')} chars")
        else:
            print(f"  Error: {result.get('error', 'Unknown error')}")

    # Analysis
    print("\n" + "-"*80)
    print("Analysis:")
    print("-"*80)

    if successful_tests:
        avg_time = sum(r["elapsed_time"] for r in successful_tests) / len(successful_tests)
        max_time = max(r["elapsed_time"] for r in successful_tests)
        min_time = min(r["elapsed_time"] for r in successful_tests)

        print(f"\nAverage response time: {avg_time:.2f}s ({avg_time/60:.2f}min)")
        print(f"Fastest response: {min_time:.2f}s ({min_time/60:.2f}min)")
        print(f"Slowest response: {max_time:.2f}s ({max_time/60:.2f}min)")

        print(f"\n4-minute limit (240s):")
        if max_time < 240:
            margin = 240 - max_time
            print(f"  ✅ All tests passed with {margin:.2f}s margin")
            print(f"  ✅ GPT-5 is suitable for deep mode")
        else:
            excess = max_time - 240
            print(f"  ⚠️  Slowest test exceeded by {excess:.2f}s")
            print(f"  ⚠️  GPT-5 may be too slow for complex questions")
            print(f"\n  Recommendations:")
            print(f"    1. Switch to faster model (Claude Sonnet 4.5, GPT-4o)")
            print(f"    2. Keep GPT-5 but document timeout risk for complex questions")
            print(f"    3. Implement automatic question decomposition")

    # Recommendation
    print("\n" + "="*80)
    print("RECOMMENDATION:")
    print("="*80)

    if len(within_limit) == len(successful_tests):
        print("\n✅ GPT-5 performs well within the 4-minute limit.")
        print("✅ Current configuration is suitable for deep mode.")
        print("\nNo changes needed to model configuration.")
    elif len(within_limit) >= len(successful_tests) * 0.66:
        print("\n⚠️  GPT-5 works for most questions but may timeout on complex ones.")
        print("\nOptions:")
        print("  A. Keep GPT-5, improve documentation about timeout risk")
        print("  B. Switch to Claude Sonnet 4.5 for better speed/quality balance")
        print("  C. Use GPT-5 mini for deep mode instead of GPT-5 full")
    else:
        print("\n❌ GPT-5 is too slow for deep mode with 4-minute limit.")
        print("\nRecommended actions:")
        print("  1. Switch deep mode to faster model:")
        print("     - Claude Sonnet 4.5 (best quality/speed balance)")
        print("     - GPT-4o (fast, good quality)")
        print("     - GPT-5 mini (already used in standard mode)")
        print("  2. Reserve GPT-5 full for custom 'ultra-deep' mode with explicit warnings")

    print("\n" + "="*80)


async def main():
    """Main entry point."""
    results = await run_all_tests()
    print_summary(results)

    # Save results to file
    import json
    from pathlib import Path

    output_file = Path(__file__).parent / "gpt5_performance_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "model": MODEL,
            "langgraph_url": LANGGRAPH_URL,
            "results": results
        }, f, indent=2)

    print(f"\n📄 Results saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
