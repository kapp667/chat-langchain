"""Benchmark HERO (Sonnet 4.5) vs PRAGMATIC (Llama 3.3 70B + PNL).

Compares quality of responses across 6 graduated questions:
- Q1 (Trivial): Single API class
- Q2 (Simple): Basic configuration
- Q3 (Moderate): Component integration
- Q4 (Moderate-complex): Debugging & resilience
- Q5 (Complex): Multi-step RAG architecture
- Q6 (Ultra-complex): Graph with backtracking

Usage:
    poetry run python mcp_server/benchmark_hero_vs_pragmatic.py --model sonnet45
    poetry run python mcp_server/benchmark_hero_vs_pragmatic.py --model llama-3.3-70b-groq
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from langgraph_sdk import get_client

# LangGraph endpoint
LANGGRAPH_URL = "http://localhost:2024"
ASSISTANT_ID = "chat"

# 6 questions graduées (simple → ultra-complexe)
BENCHMARK_QUESTIONS = [
    {
        "id": "q1_trivial",
        "complexity": "trivial",
        "category": "API lookup",
        "question": "I need to save conversation history to PostgreSQL. Which class should I use?",
        "expected_answer_length": "1-5 lines",
        "expected_components": ["AsyncPostgresSaver", "PostgresSaver"]
    },
    {
        "id": "q2_simple",
        "complexity": "simple",
        "category": "Configuration",
        "question": "How do I configure LangGraph to use my own OpenAI API key and custom temperature?",
        "expected_answer_length": "5-15 lines",
        "expected_components": ["OPENAI_API_KEY", "temperature", "ChatOpenAI"]
    },
    {
        "id": "q3_moderate",
        "complexity": "moderate",
        "category": "Component integration",
        "question": "I want to build a chatbot that remembers previous messages across sessions. What components do I need and how do I connect them?",
        "expected_answer_length": "20-40 lines",
        "expected_components": ["checkpointer", "thread_id", "StateGraph", "memory"]
    },
    {
        "id": "q4_moderate_complex",
        "complexity": "moderate-complex",
        "category": "Debugging & resilience",
        "question": "My LangGraph agent keeps timing out after 30 seconds on complex questions. How can I debug this and make it more resilient?",
        "expected_answer_length": "30-60 lines",
        "expected_components": ["timeout", "recursion_limit", "streaming", "error handling"]
    },
    {
        "id": "q5_complex",
        "complexity": "complex",
        "category": "Multi-step architecture",
        "question": "I need to build a research assistant that: (1) breaks down complex questions into sub-questions, (2) searches documentation for each sub-question, (3) synthesizes findings. How should I structure this?",
        "expected_answer_length": "50-120 lines",
        "expected_components": ["StateGraph", "nodes", "conditional edges", "multi-query", "synthesis"]
    },
    {
        "id": "q6_ultra_complex",
        "complexity": "ultra-complex",
        "category": "Advanced graph with backtracking",
        "question": "I want to create a planning agent that explores multiple solution paths, can backtrack when hitting dead ends, and maintains a tree of attempted strategies. How do I implement this with LangGraph?",
        "expected_answer_length": "100-250 lines",
        "expected_components": ["StateGraph", "checkpoints", "time travel", "conditional routing", "state management", "backtracking"]
    }
]

# Model configurations
MODELS = {
    "sonnet45": {
        "id": "anthropic/claude-sonnet-4-5-20250929",
        "name": "Claude Sonnet 4.5 (HERO)",
        "description": "Excellence maximale (champion qualité)",
        "expected_speed": "slow (40-120s)",
        "expected_quality": "5/5"
    },
    "llama-3.3-70b-groq": {
        "id": "groq/llama-3.3-70b-versatile",
        "name": "Llama 3.3 70B + PNL (PRAGMATIC)",
        "description": "Compromis optimal vitesse/qualité (avec anti-hallucination PNL)",
        "expected_speed": "fast (8-15s)",
        "expected_quality": "4.6/5"
    }
}


async def invoke_graph(question: str, model_id: str) -> Dict:
    """Invoke LangGraph with specific model and question."""
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
                "content": question
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

        # Extract messages
        if hasattr(chunk, "data") and chunk.data:
            if isinstance(chunk.data, list):
                last_messages = chunk.data
            elif isinstance(chunk.data, dict) and "messages" in chunk.data:
                last_messages = chunk.data["messages"]

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

    return {
        "output": {
            "messages": [
                {"role": "assistant", "content": response_text}
            ]
        },
        "chunk_count": chunk_count
    }


async def run_benchmark_question(
    question_data: Dict,
    model_key: str
) -> Dict:
    """Run single benchmark question."""
    model_config = MODELS[model_key]
    model_id = model_config["id"]

    print(f"\n{'='*80}")
    print(f"Question {question_data['id']} ({question_data['complexity'].upper()})")
    print(f"Model: {model_config['name']}")
    print(f"{'='*80}")
    print(f"Q: {question_data['question']}")
    print(f"\nInvoking LangGraph endpoint...")

    start_time = time.time()
    start_timestamp = datetime.now().isoformat()

    try:
        result = await invoke_graph(question_data["question"], model_id)
        elapsed_time = time.time() - start_time
        end_timestamp = datetime.now().isoformat()

        # Extract response from LangGraph output
        messages = result.get("output", {}).get("messages", [])
        if not messages:
            raise ValueError("No messages in response")

        # Last message is AI response
        ai_response = messages[-1].get("content", "")

        # Extract metadata
        chunk_count = result.get("chunk_count", 0)
        response_length = len(ai_response)

        print(f"\n✓ Completed in {elapsed_time:.2f}s")
        print(f"  Response length: {response_length} chars")
        print(f"  Chunks retrieved: {chunk_count}")
        print(f"  First 500 chars: {ai_response[:500]}...")

        return {
            "question_id": question_data["id"],
            "complexity": question_data["complexity"],
            "category": question_data["category"],
            "question": question_data["question"],
            "success": True,
            "elapsed_time": elapsed_time,
            "elapsed_minutes": elapsed_time / 60,
            "start_time": start_timestamp,
            "end_time": end_timestamp,
            "response_full": ai_response,
            "response_length": response_length,
            "chunk_count": chunk_count,
            "error": None
        }

    except Exception as e:
        elapsed_time = time.time() - start_time
        end_timestamp = datetime.now().isoformat()

        print(f"\n✗ Failed after {elapsed_time:.2f}s")
        print(f"  Error: {str(e)}")

        return {
            "question_id": question_data["id"],
            "complexity": question_data["complexity"],
            "category": question_data["category"],
            "question": question_data["question"],
            "success": False,
            "elapsed_time": elapsed_time,
            "elapsed_minutes": elapsed_time / 60,
            "start_time": start_timestamp,
            "end_time": end_timestamp,
            "response_full": "",
            "response_length": 0,
            "chunk_count": 0,
            "error": str(e)
        }


async def run_full_benchmark(model_key: str):
    """Run complete benchmark (6 questions) for one model."""
    model_config = MODELS[model_key]

    print(f"\n{'#'*80}")
    print(f"# BENCHMARK: {model_config['name']}")
    print(f"# {model_config['description']}")
    print(f"# Expected: {model_config['expected_speed']}, {model_config['expected_quality']}")
    print(f"{'#'*80}\n")

    results = []
    for question_data in BENCHMARK_QUESTIONS:
        result = await run_benchmark_question(question_data, model_key)
        results.append(result)

        # Small delay between questions
        await asyncio.sleep(2)

    # Calculate statistics
    successful_results = [r for r in results if r["success"]]
    total_tests = len(results)
    successful_tests = len(successful_results)
    failed_tests = total_tests - successful_tests

    if successful_results:
        times = [r["elapsed_time"] for r in successful_results]
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        lengths = [r["response_length"] for r in successful_results]
        avg_length = sum(lengths) / len(lengths)
        min_length = min(lengths)
        max_length = max(lengths)
    else:
        avg_time = min_time = max_time = 0
        avg_length = min_length = max_length = 0

    # Build final report
    report = {
        "timestamp": datetime.now().isoformat(),
        "model_key": model_key,
        "model_name": model_config["name"],
        "model_id": model_config["id"],
        "model_description": model_config["description"],
        "langgraph_url": LANGGRAPH_URL,
        "total_tests": total_tests,
        "successful_tests": successful_tests,
        "failed_tests": failed_tests,
        "statistics": {
            "average_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "average_minutes": avg_time / 60,
            "min_minutes": min_time / 60,
            "max_minutes": max_time / 60,
            "average_response_length": avg_length,
            "min_response_length": min_length,
            "max_response_length": max_length
        },
        "results": results
    }

    # Save to file
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"hero_vs_pragmatic_{model_key}_results.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"BENCHMARK COMPLETE: {model_config['name']}")
    print(f"{'='*80}")
    print(f"Total tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {failed_tests}")
    print(f"\nPerformance:")
    print(f"  Average time: {avg_time:.2f}s ({avg_time/60:.2f} min)")
    print(f"  Min time: {min_time:.2f}s")
    print(f"  Max time: {max_time:.2f}s")
    print(f"\nResponse quality:")
    print(f"  Average length: {avg_length:.0f} chars")
    print(f"  Min length: {min_length:.0f} chars")
    print(f"  Max length: {max_length:.0f} chars")
    print(f"\nResults saved to: {output_file}")
    print(f"{'='*80}\n")

    return report


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark HERO vs PRAGMATIC")
    parser.add_argument(
        "--model",
        choices=list(MODELS.keys()),
        required=True,
        help="Model to benchmark"
    )
    args = parser.parse_args()

    asyncio.run(run_full_benchmark(args.model))


if __name__ == "__main__":
    main()
