#!/usr/bin/env python3
"""Empirical benchmarking script for comparing LLM models on LangChain questions.

This script tests multiple models (GPT-5, GPT-5 Mini, Claude Sonnet 4.5, DeepSeek Reasoner)
on the same questions to measure both speed and quality empirically.

Usage:
    poetry run python mcp_server/benchmark_models.py --model gpt5-full
    poetry run python mcp_server/benchmark_models.py --model gpt5-mini
    poetry run python mcp_server/benchmark_models.py --model sonnet45
    poetry run python mcp_server/benchmark_models.py --model deepseek-reasoner
"""

import argparse
import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from langgraph_sdk import get_client

# Configuration
LANGGRAPH_URL = "http://localhost:2024"
ASSISTANT_ID = "chat"

# Model configurations
MODELS = {
    "gpt5-full": {
        "id": "openai/gpt-5-2025-08-07",
        "name": "GPT-5 Full",
        "description": "OpenAI GPT-5 (full reasoning)",
        "expected_speed": "slow (~180-250s complex)",
        "expected_quality": "excellent"
    },
    "gpt5-mini": {
        "id": "openai/gpt-5-mini-2025-08-07",
        "name": "GPT-5 Mini",
        "description": "OpenAI GPT-5 Mini (faster, cost-effective)",
        "expected_speed": "fast (~60-120s complex)",
        "expected_quality": "very good"
    },
    "sonnet45": {
        "id": "anthropic/claude-sonnet-4-5-20250929",
        "name": "Claude Sonnet 4.5",
        "description": "Anthropic Claude Sonnet 4.5 (latest)",
        "expected_speed": "fast (~80-150s complex)",
        "expected_quality": "excellent"
    },
    "deepseek-chat": {
        "id": "deepseek/deepseek-chat",
        "name": "DeepSeek Chat (V3)",
        "description": "DeepSeek V3.2-Exp (supports tool calling & structured output)",
        "expected_speed": "fast (~60-120s complex)",
        "expected_quality": "excellent"
    }
}

# Test questions (identical for all models)
TEST_QUESTIONS = [
    {
        "id": "test_1_simple",
        "question": "What is LangGraph and how does it differ from LangChain?",
        "complexity": "simple",
        "expected_time_range": "30-120s",
        "description": "Simple factual question with basic comparison"
    },
    {
        "id": "test_2_moderate",
        "question": "Explain how LangGraph checkpoints work with PostgreSQL, including the AsyncPostgresSaver class and how to handle migration between checkpoint versions.",
        "complexity": "moderate",
        "expected_time_range": "60-180s",
        "description": "Detailed technical question requiring multiple doc sections"
    },
    {
        "id": "test_3_complex",
        "question": "Design a production-grade multi-agent LangGraph system with the following requirements: (1) human-in-the-loop approval for critical decisions, (2) PostgreSQL checkpoints for state persistence, (3) error recovery and retry logic, (4) observability with LangSmith, and (5) deployment strategy. Provide architectural decisions and code examples.",
        "complexity": "complex",
        "expected_time_range": "120-300s",
        "description": "Multi-step architecture question requiring deep reasoning"
    }
]


async def run_single_test(test_config: Dict, model_id: str, model_name: str) -> Dict:
    """Run a single test and measure response time + save full response.

    Args:
        test_config: Test configuration with question and metadata
        model_id: Model identifier (e.g., "openai/gpt-5-2025-08-07")
        model_name: Human-readable model name

    Returns:
        Dictionary with test results including timing and FULL response
    """
    print(f"\n{'='*80}")
    print(f"Test: {test_config['id']}")
    print(f"Model: {model_name}")
    print(f"Complexity: {test_config['complexity']}")
    print(f"Expected: {test_config['expected_time_range']}")
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

        # Configure model
        config = {
            "configurable": {
                "query_model": model_id,
                "response_model": model_id
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
        progress_interval = 10

        async for chunk in client.runs.stream(
            thread_id,
            ASSISTANT_ID,
            input=input_data,
            config=config,
            stream_mode="messages"
        ):
            chunk_count += 1

            # Print progress
            if chunk_count % progress_interval == 0:
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

        # Extract final response (FULL TEXT, not truncated)
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
            "question": test_config["question"],
            "success": True,
            "elapsed_time": elapsed_time,
            "elapsed_minutes": elapsed_time / 60,
            "within_limit": within_limit,
            "chunk_count": chunk_count,
            "response_length": len(response_text),
            "start_time": start_datetime,
            "end_time": end_datetime,
            "response_full": response_text  # FULL RESPONSE, not truncated
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
            "question": test_config["question"],
            "success": False,
            "elapsed_time": elapsed_time,
            "elapsed_minutes": elapsed_time / 60,
            "within_limit": False,
            "error": f"{type(e).__name__}: {str(e)}"
        }


async def run_all_tests(model_key: str) -> Dict:
    """Run all performance tests for a specific model.

    Args:
        model_key: Model key from MODELS dict (e.g., "gpt5-full")

    Returns:
        Dictionary with all test results and metadata
    """
    if model_key not in MODELS:
        raise ValueError(f"Unknown model: {model_key}. Available: {list(MODELS.keys())}")

    model_config = MODELS[model_key]
    model_id = model_config["id"]
    model_name = model_config["name"]

    print("\n" + "="*80)
    print(f"BENCHMARKING: {model_name}")
    print("="*80)
    print(f"\nModel ID: {model_id}")
    print(f"Description: {model_config['description']}")
    print(f"Expected Speed: {model_config['expected_speed']}")
    print(f"Expected Quality: {model_config['expected_quality']}")
    print(f"Target: <240 seconds (4 minutes) per question")
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
        return {
            "model_key": model_key,
            "model_name": model_name,
            "model_id": model_id,
            "error": f"Cannot connect to LangGraph: {str(e)}",
            "results": []
        }

    results = []

    for i, test_config in enumerate(TEST_QUESTIONS, 1):
        print(f"\n\n{'#'*80}")
        print(f"# Test {i}/{len(TEST_QUESTIONS)}: {test_config['complexity'].upper()}")
        print(f"{'#'*80}")

        result = await run_single_test(test_config, model_id, model_name)
        results.append(result)

        # Wait between tests to avoid rate limits
        if i < len(TEST_QUESTIONS):
            print(f"\n⏸️  Waiting 5 seconds before next test...")
            await asyncio.sleep(5)

    # Calculate statistics
    successful_tests = [r for r in results if r.get("success", False)]
    failed_tests = [r for r in results if not r.get("success", False)]
    within_limit = [r for r in successful_tests if r.get("within_limit", False)]

    if successful_tests:
        avg_time = sum(r["elapsed_time"] for r in successful_tests) / len(successful_tests)
        max_time = max(r["elapsed_time"] for r in successful_tests)
        min_time = min(r["elapsed_time"] for r in successful_tests)
    else:
        avg_time = max_time = min_time = 0

    return {
        "timestamp": datetime.now().isoformat(),
        "model_key": model_key,
        "model_name": model_name,
        "model_id": model_id,
        "model_description": model_config["description"],
        "langgraph_url": LANGGRAPH_URL,
        "total_tests": len(results),
        "successful_tests": len(successful_tests),
        "failed_tests": len(failed_tests),
        "within_limit_tests": len(within_limit),
        "statistics": {
            "average_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "average_minutes": avg_time / 60,
            "min_minutes": min_time / 60,
            "max_minutes": max_time / 60
        },
        "results": results
    }


def print_summary(data: Dict):
    """Print summary of all test results.

    Args:
        data: Test results data
    """
    print("\n\n" + "="*80)
    print(f"SUMMARY: {data['model_name']} Performance Test Results")
    print("="*80)

    if "error" in data:
        print(f"\n❌ Error: {data['error']}")
        return

    results = data["results"]
    stats = data["statistics"]

    print(f"\nModel: {data['model_name']} ({data['model_id']})")
    print(f"Tests completed: {data['total_tests']}")
    print(f"✅ Successful: {data['successful_tests']}")
    print(f"❌ Failed: {data['failed_tests']}")
    print(f"✅ Within 4min limit: {data['within_limit_tests']}/{data['successful_tests']}")

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

    # Statistics
    if data["successful_tests"] > 0:
        print("\n" + "-"*80)
        print("Statistics:")
        print("-"*80)

        print(f"\nAverage response time: {stats['average_time']:.2f}s ({stats['average_minutes']:.2f}min)")
        print(f"Fastest response: {stats['min_time']:.2f}s ({stats['min_minutes']:.2f}min)")
        print(f"Slowest response: {stats['max_time']:.2f}s ({stats['max_minutes']:.2f}min)")

        print(f"\n4-minute limit (240s):")
        if stats["max_time"] < 240:
            margin = 240 - stats["max_time"]
            print(f"  ✅ All tests passed with {margin:.2f}s margin")
            print(f"  ✅ {data['model_name']} is suitable for deep mode")
        else:
            excess = stats["max_time"] - 240
            print(f"  ⚠️  Slowest test exceeded by {excess:.2f}s")
            print(f"  ⚠️  {data['model_name']} may timeout on complex questions")

    print("\n" + "="*80)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Benchmark LLM models on LangChain questions")
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        choices=list(MODELS.keys()),
        help=f"Model to benchmark: {', '.join(MODELS.keys())}"
    )
    args = parser.parse_args()

    # Run tests
    data = await run_all_tests(args.model)

    # Print summary
    print_summary(data)

    # Save results to file
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / f"{args.model}_results.json"
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\n📄 Results saved to: {output_file}")
    print(f"📊 Full responses saved (not truncated)")


if __name__ == "__main__":
    asyncio.run(main())
