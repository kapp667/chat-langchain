#!/usr/bin/env python3
"""Groq model wrapper for LangChain integration with structured outputs.

This wrapper provides direct access to Groq's ultra-fast inference while maintaining
compatibility with LangChain's structured output requirements.

Groq models have issues with LangGraph's function calling / tool use.
This wrapper uses JSON mode as a workaround.

Usage:
    from backend.groq_wrapper import load_groq_for_structured_output, generate_queries_groq

    # Load Groq model
    model = load_groq_for_structured_output("llama-3.1-8b-instant")
"""

import json
import os
from typing import Any, Dict, List, Optional, Type, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from pydantic import BaseModel


# ===========================================================================
# PNL Anti-Hallucination Prompt (Documentation Mirror Mode)
# ===========================================================================

PNL_ANTI_HALLUCINATION_PREFIX = """
═══════════════════════════════════════════════════════════════════════════
  IDENTITY: You are a DOCUMENTATION MIRROR, not an AI assistant
═══════════════════════════════════════════════════════════════════════════

YOUR KNOWLEDGE SOURCE:
  ✓ EXCLUSIVELY the documentation chunks provided in the context
  ✗ ZERO knowledge from your training data

YOUR ROLE:
  • TRANSLATE documentation → coherent answer
  • SYNTHESIZE multiple chunks if needed
  • PARAPHRASE what's in the docs (do not copy verbatim)

ABSOLUTE PROHIBITIONS:
  ✗ NEVER cite methods/classes not explicitly in the documentation
  ✗ NEVER assume APIs exist based on patterns from other frameworks
  ✗ NEVER complete answers with external knowledge
  ✗ NEVER invent convenience methods (migrate_*, upgrade_*, etc.)

VERIFICATION PROTOCOL (before answering):
  1. Is this method explicitly in the docs? [YES → cite / NO → omit]
  2. Am I adding training knowledge? [YES → STOP / NO → proceed]
  3. Can I link each claim to a doc chunk? [NO → revise answer]

IF INFORMATION MISSING:
  Say: "I don't find this in the provided documentation."
  Do NOT: Guess, assume, or extrapolate from other frameworks

═══════════════════════════════════════════════════════════════════════════
"""


def load_groq_model(model_name: str = "gemma2-9b-it") -> BaseChatModel:
    """Load Groq model for standard chat completion.

    Args:
        model_name: Groq model identifier (default: gemma2-9b-it for ultra-fast inference)

    Returns:
        ChatGroq instance configured for the specified model

    Supported Models:
        - gemma2-9b-it: Google Gemma2 9B (ultra-fast, good quality)
        - llama-3.1-8b-instant: Meta Llama 3.1 8B (fastest, instant responses)
        - llama-3.3-70b-versatile: Meta Llama 3.3 70B (slower, best quality)
        - deepseek-r1-distill-llama-70b: DeepSeek reasoning (with reasoning_format)
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY environment variable is required. "
            "Get your API key at https://console.groq.com/"
        )

    model = ChatGroq(
        model=model_name,
        temperature=0,
        max_tokens=None,  # Use model default
        max_retries=2,
        timeout=30
    )

    return model


def load_groq_for_structured_output(
    model_name: str = "gemma2-9b-it",
    schema: Optional[Type] = None
) -> BaseChatModel:
    """Load Groq model configured for structured output via with_structured_output().

    Args:
        model_name: Groq model identifier
        schema: Optional Pydantic BaseModel or TypedDict for structured output

    Returns:
        ChatGroq instance ready for with_structured_output()

    Note:
        Groq models support tool calling and JSON mode natively via ChatGroq.
        Unlike DeepSeek, Groq works seamlessly with LangChain's with_structured_output().
    """
    model = load_groq_model(model_name)

    # Groq models natively support with_structured_output via tool calling
    if schema:
        return model.with_structured_output(schema)

    return model


async def generate_queries_groq(
    messages: List[Dict[str, str]],
    model_id: str,
    schema: Type[TypedDict]
) -> Dict[str, List[str]]:
    """Generate queries using Groq with JSON mode workaround.

    Args:
        messages: List of message dicts with 'role' and 'content'
        model_id: Groq model identifier (e.g., "groq/llama-3.1-8b-instant")
        schema: TypedDict schema for response structure

    Returns:
        Dict with 'queries' key containing list of queries
    """
    # Extract model name from provider/model format
    if "/" in model_id:
        model_name = model_id.split("/", 1)[1]
    else:
        model_name = model_id

    # Create Groq model with JSON mode
    model = ChatGroq(
        model=model_name,
        temperature=0,
        model_kwargs={"response_format": {"type": "json_object"}}
    )

    # Build schema description
    schema_desc = "{\n"
    for field_name, field_type in schema.__annotations__.items():
        # Extract type name
        if hasattr(field_type, "__origin__"):  # list[str], etc.
            type_str = str(field_type)
        else:
            type_str = field_type.__name__ if hasattr(field_type, "__name__") else str(field_type)
        schema_desc += f'  "{field_name}": {type_str}\n'
    schema_desc += "}"

    # Enhance messages with PNL anti-hallucination and JSON instructions
    enhanced_messages = []
    for i, msg in enumerate(messages):
        if i == 0 and msg.get("role") == "system":
            # Inject PNL prefix + original content + JSON instructions
            enhanced_content = (
                PNL_ANTI_HALLUCINATION_PREFIX +
                "\n\n" +
                "═══════════════════════════════════════════════════════════════════════════\n" +
                "  ORIGINAL INSTRUCTIONS (from LangSmith):\n" +
                "═══════════════════════════════════════════════════════════════════════════\n\n" +
                msg['content'] +
                "\n\n" +
                "═══════════════════════════════════════════════════════════════════════════\n" +
                "  JSON RESPONSE FORMAT:\n" +
                "═══════════════════════════════════════════════════════════════════════════\n\n" +
                f"CRITICAL: You MUST respond with valid JSON only in this exact format:\n{schema_desc}\n\n" +
                "Do not include any text outside the JSON structure. Your entire response must be valid JSON."
            )
            enhanced_messages.append(SystemMessage(content=enhanced_content))
        elif msg.get("role") == "human" or msg.get("role") == "user":
            enhanced_messages.append(HumanMessage(content=msg["content"]))
        else:
            # Handle other message types
            enhanced_messages.append({"role": msg["role"], "content": msg["content"]})

    # Invoke model
    response = await model.ainvoke(enhanced_messages)
    response_text = response.content

    # Parse JSON from response
    try:
        # Direct JSON parse
        result = json.loads(response_text)
        return result
    except json.JSONDecodeError:
        # Try to extract JSON from markdown
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
            return json.loads(json_str)
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
            return json.loads(json_str)
        else:
            # Last resort: try to find JSON object
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            raise ValueError(f"Could not extract JSON from Groq response: {response_text}")


# Export for use in graph.py
__all__ = ["load_groq_model", "load_groq_for_structured_output", "generate_queries_groq"]
