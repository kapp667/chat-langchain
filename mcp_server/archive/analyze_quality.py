#!/usr/bin/env python3
"""
Quality Analysis Script for Model Benchmark Results

Compares GPT-5 Full vs GPT-5 Mini responses on 5 quality criteria:
1. Accuracy - Technical correctness of information
2. Completeness - Coverage of all question aspects
3. Code Quality - Examples, best practices, implementation details
4. Structure - Organization, clarity, readability
5. Citations - Source references, documentation links

Uses LLM inference to generate objective quality scores (1-5 scale).
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List
from langgraph_sdk import get_client

# Quality evaluation criteria
QUALITY_CRITERIA = {
    "accuracy": {
        "name": "Technical Accuracy",
        "description": "Correctness of technical information, API usage, and concepts",
        "weight": 0.30
    },
    "completeness": {
        "name": "Completeness",
        "description": "Coverage of all aspects mentioned in the question",
        "weight": 0.25
    },
    "code_quality": {
        "name": "Code Quality",
        "description": "Quality of code examples, best practices, implementation details",
        "weight": 0.20
    },
    "structure": {
        "name": "Structure & Clarity",
        "description": "Organization, readability, logical flow",
        "weight": 0.15
    },
    "citations": {
        "name": "Citations & Sources",
        "description": "References to documentation, source code, examples",
        "weight": 0.10
    }
}

EVALUATION_PROMPT_TEMPLATE = """You are an expert technical evaluator assessing LangGraph/LangChain documentation responses.

**Question:**
{question}

**Response to Evaluate:**
{response}

**Evaluation Criterion: {criterion_name}**
{criterion_description}

**Scoring Guidelines (1-5 scale):**
- **5 (Excellent)**: {criterion_5}
- **4 (Good)**: {criterion_4}
- **3 (Adequate)**: {criterion_3}
- **2 (Poor)**: {criterion_2}
- **1 (Very Poor)**: {criterion_1}

**Task:**
1. Analyze the response according to the criterion
2. Provide specific examples from the response
3. Assign a score (1-5)
4. Explain your reasoning in 2-3 sentences

**Output Format (JSON):**
```json
{{
  "score": <1-5>,
  "reasoning": "<explanation>",
  "examples": ["<specific example 1>", "<specific example 2>"]
}}
```

Provide ONLY the JSON output, no additional text.
"""

# Criterion-specific scoring guidelines
CRITERION_GUIDELINES = {
    "accuracy": {
        "5": "All technical details correct, APIs used properly, concepts explained accurately",
        "4": "Mostly correct with minor inaccuracies that don't affect understanding",
        "3": "Generally correct but some notable errors or outdated information",
        "2": "Multiple significant errors or misconceptions",
        "1": "Fundamentally incorrect information"
    },
    "completeness": {
        "5": "Addresses all aspects of the question thoroughly with relevant details",
        "4": "Covers main aspects well, minor points may be missing",
        "3": "Addresses core question but misses some important aspects",
        "2": "Incomplete, misses several key aspects",
        "1": "Fails to address most of the question"
    },
    "code_quality": {
        "5": "Excellent code examples, best practices, production-ready patterns",
        "4": "Good code examples with minor improvements possible",
        "3": "Basic code examples, functional but could be better",
        "2": "Poor code quality or minimal examples",
        "1": "No code examples or incorrect code"
    },
    "structure": {
        "5": "Exceptionally well-organized, clear headers, logical flow, easy to follow",
        "4": "Well-structured with good organization and clarity",
        "3": "Adequate structure, could be clearer or better organized",
        "2": "Poorly organized, hard to follow",
        "1": "Confusing structure, no clear organization"
    },
    "citations": {
        "5": "Excellent references to docs, source code, and examples with links",
        "4": "Good citations with most sources referenced",
        "3": "Some citations but incomplete or lacking links",
        "2": "Minimal citations, hard to verify claims",
        "1": "No citations or references"
    }
}


async def evaluate_response(
    question: str,
    response: str,
    criterion_key: str,
    model_id: str = "openai/gpt-5-mini-2025-08-07"
) -> Dict:
    """
    Evaluate a response on a single quality criterion using LLM inference.

    Args:
        question: The original test question
        response: The model's response to evaluate
        criterion_key: Key of the criterion (e.g., "accuracy")
        model_id: LLM to use for evaluation (default: GPT-5 Mini for speed)

    Returns:
        Dict with score, reasoning, and examples
    """
    criterion = QUALITY_CRITERIA[criterion_key]
    guidelines = CRITERION_GUIDELINES[criterion_key]

    prompt = EVALUATION_PROMPT_TEMPLATE.format(
        question=question,
        response=response,
        criterion_name=criterion["name"],
        criterion_description=criterion["description"],
        criterion_5=guidelines["5"],
        criterion_4=guidelines["4"],
        criterion_3=guidelines["3"],
        criterion_2=guidelines["2"],
        criterion_1=guidelines["1"]
    )

    client = get_client(url="http://localhost:2024")

    # Create assistant for evaluation
    assistant = await client.assistants.create(
        graph_id="agent",
        config={
            "configurable": {
                "model": model_id,
                "response_type": "quick"  # Use quick mode for evaluation
            }
        }
    )

    # Create thread
    thread = await client.threads.create()

    # Run evaluation
    full_response = ""
    async for chunk in client.runs.stream(
        thread["thread_id"],
        assistant["assistant_id"],
        input={"messages": [{"role": "user", "content": prompt}]},
        stream_mode="messages"
    ):
        if chunk.event == "messages/partial":
            for message in chunk.data:
                if message.get("role") == "assistant":
                    content = message.get("content", [])
                    if content and isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and item.get("type") == "text":
                                full_response = item.get("text", "")

    # Parse JSON response
    try:
        # Extract JSON from markdown code block if present
        if "```json" in full_response:
            json_start = full_response.index("```json") + 7
            json_end = full_response.index("```", json_start)
            json_str = full_response[json_start:json_end].strip()
        else:
            json_str = full_response.strip()

        result = json.loads(json_str)

        return {
            "criterion": criterion_key,
            "criterion_name": criterion["name"],
            "score": result.get("score", 0),
            "reasoning": result.get("reasoning", ""),
            "examples": result.get("examples", []),
            "weight": criterion["weight"]
        }
    except (json.JSONDecodeError, ValueError) as e:
        print(f"⚠️  Failed to parse evaluation result for {criterion_key}: {e}")
        print(f"Raw response: {full_response[:200]}...")
        return {
            "criterion": criterion_key,
            "criterion_name": criterion["name"],
            "score": 0,
            "reasoning": f"Evaluation failed: {str(e)}",
            "examples": [],
            "weight": criterion["weight"]
        }


async def compare_responses(
    question: str,
    response_a: str,
    response_b: str,
    model_a_name: str,
    model_b_name: str
) -> Dict:
    """
    Compare two responses on all quality criteria.

    Returns:
        Dict with detailed comparison results
    """
    print(f"\n📊 Comparing responses for question: {question[:80]}...")

    results = {
        "question": question,
        "model_a": model_a_name,
        "model_b": model_b_name,
        "evaluations_a": [],
        "evaluations_b": [],
        "scores_a": {},
        "scores_b": {},
        "weighted_score_a": 0.0,
        "weighted_score_b": 0.0,
        "winner": None
    }

    # Evaluate both responses on all criteria
    for criterion_key in QUALITY_CRITERIA.keys():
        print(f"  Evaluating: {QUALITY_CRITERIA[criterion_key]['name']}...")

        # Evaluate response A
        eval_a = await evaluate_response(question, response_a, criterion_key)
        results["evaluations_a"].append(eval_a)
        results["scores_a"][criterion_key] = eval_a["score"]

        # Evaluate response B
        eval_b = await evaluate_response(question, response_b, criterion_key)
        results["evaluations_b"].append(eval_b)
        results["scores_b"][criterion_key] = eval_b["score"]

        print(f"    {model_a_name}: {eval_a['score']}/5")
        print(f"    {model_b_name}: {eval_b['score']}/5")

    # Calculate weighted scores
    for eval_item in results["evaluations_a"]:
        results["weighted_score_a"] += eval_item["score"] * eval_item["weight"]

    for eval_item in results["evaluations_b"]:
        results["weighted_score_b"] += eval_item["score"] * eval_item["weight"]

    # Determine winner
    if results["weighted_score_a"] > results["weighted_score_b"]:
        results["winner"] = model_a_name
    elif results["weighted_score_b"] > results["weighted_score_a"]:
        results["winner"] = model_b_name
    else:
        results["winner"] = "TIE"

    return results


async def analyze_all_questions():
    """
    Load benchmark results and perform comprehensive quality analysis.
    """
    results_dir = Path(__file__).parent / "results"

    # Load benchmark results
    with open(results_dir / "gpt5-full_results.json") as f:
        gpt5_full_data = json.load(f)

    with open(results_dir / "gpt5-mini_results.json") as f:
        gpt5_mini_data = json.load(f)

    print("=" * 80)
    print("🔬 QUALITY ANALYSIS: GPT-5 Full vs GPT-5 Mini")
    print("=" * 80)
    print(f"\nModel A: {gpt5_full_data['model_name']} ({gpt5_full_data['model_id']})")
    print(f"Model B: {gpt5_mini_data['model_name']} ({gpt5_mini_data['model_id']})")
    print(f"\nTotal questions: {len(gpt5_full_data['results'])}")

    all_comparisons = []

    # Compare each question
    for i, (result_full, result_mini) in enumerate(zip(
        gpt5_full_data["results"],
        gpt5_mini_data["results"]
    )):
        print(f"\n{'=' * 80}")
        print(f"Question {i+1}/{len(gpt5_full_data['results'])}: {result_full['complexity'].upper()}")
        print(f"{'=' * 80}")

        comparison = await compare_responses(
            question=result_full["question"],
            response_a=result_full["response_full"],
            response_b=result_mini["response_full"],
            model_a_name=gpt5_full_data["model_name"],
            model_b_name=gpt5_mini_data["model_name"]
        )

        all_comparisons.append(comparison)

        # Print summary
        print(f"\n📈 Summary for this question:")
        print(f"  {gpt5_full_data['model_name']}: {comparison['weighted_score_a']:.2f}/5.0")
        print(f"  {gpt5_mini_data['model_name']}: {comparison['weighted_score_b']:.2f}/5.0")
        print(f"  Winner: {comparison['winner']}")

    # Calculate overall statistics
    overall_stats = {
        "timestamp": gpt5_full_data["timestamp"],
        "model_a_name": gpt5_full_data["model_name"],
        "model_b_name": gpt5_mini_data["model_name"],
        "total_questions": len(all_comparisons),
        "comparisons": all_comparisons,
        "average_score_a": sum(c["weighted_score_a"] for c in all_comparisons) / len(all_comparisons),
        "average_score_b": sum(c["weighted_score_b"] for c in all_comparisons) / len(all_comparisons),
        "wins_a": sum(1 for c in all_comparisons if c["winner"] == gpt5_full_data["model_name"]),
        "wins_b": sum(1 for c in all_comparisons if c["winner"] == gpt5_mini_data["model_name"]),
        "ties": sum(1 for c in all_comparisons if c["winner"] == "TIE")
    }

    # Determine overall winner
    if overall_stats["average_score_a"] > overall_stats["average_score_b"]:
        overall_stats["overall_winner"] = gpt5_full_data["model_name"]
    elif overall_stats["average_score_b"] > overall_stats["average_score_a"]:
        overall_stats["overall_winner"] = gpt5_mini_data["model_name"]
    else:
        overall_stats["overall_winner"] = "TIE"

    # Save results
    output_file = results_dir / "quality_analysis.json"
    with open(output_file, "w") as f:
        json.dump(overall_stats, f, indent=2)

    print(f"\n{'=' * 80}")
    print("🏆 OVERALL QUALITY COMPARISON")
    print(f"{'=' * 80}")
    print(f"\nAverage Scores (weighted):")
    print(f"  {gpt5_full_data['model_name']}: {overall_stats['average_score_a']:.2f}/5.0")
    print(f"  {gpt5_mini_data['model_name']}: {overall_stats['average_score_b']:.2f}/5.0")
    print(f"\nQuestion Wins:")
    print(f"  {gpt5_full_data['model_name']}: {overall_stats['wins_a']}/{overall_stats['total_questions']}")
    print(f"  {gpt5_mini_data['model_name']}: {overall_stats['wins_b']}/{overall_stats['total_questions']}")
    print(f"  Ties: {overall_stats['ties']}/{overall_stats['total_questions']}")
    print(f"\n🏆 Overall Winner: {overall_stats['overall_winner']}")
    print(f"\n✅ Results saved to: {output_file}")

    return overall_stats


if __name__ == "__main__":
    asyncio.run(analyze_all_questions())
