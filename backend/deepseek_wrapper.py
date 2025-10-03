"""DeepSeek model wrapper with enhanced structured output support.

This wrapper addresses DeepSeek's specific requirements for JSON mode:
1. Explicit response_format={'type': 'json_object'} parameter
2. Enhanced prompts with JSON format instructions
3. Fallback extraction from markdown code blocks

Usage:
    from backend.deepseek_wrapper import load_deepseek_for_structured_output

    model = load_deepseek_for_structured_output("deepseek/deepseek-chat")
    response = await model.ainvoke(messages)
"""

import json
import re
from typing import Any, Dict, List, Optional, Type

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_core.pydantic_v1 import BaseModel
from langchain_deepseek import ChatDeepSeek


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


def enhance_prompt_for_json(
    messages: List[BaseMessage],
    schema: Optional[Type[BaseModel]] = None
) -> List[BaseMessage]:
    """Enhance messages with JSON format instructions for DeepSeek.

    DeepSeek requires:
    - The word "json" in the prompt
    - An example of the expected format
    - Explicit instructions to return ONLY JSON

    Args:
        messages: Original messages
        schema: Optional Pydantic model defining the expected structure

    Returns:
        Enhanced messages with JSON instructions
    """
    enhanced = list(messages)

    # Build JSON instruction based on schema if provided
    if schema:
        # Handle both Pydantic BaseModel and TypedDict
        if hasattr(schema, 'schema'):
            # Pydantic BaseModel
            schema_json = schema.schema()
        elif hasattr(schema, '__annotations__'):
            # TypedDict - manually construct schema
            schema_json = {
                "properties": {
                    field_name: {"type": _get_type_name(field_type)}
                    for field_name, field_type in schema.__annotations__.items()
                }
            }
        else:
            # Unknown schema type, skip example generation
            schema_json = {}
        example = _generate_example_from_schema(schema_json)
        json_instruction = f"""
CRITICAL: You MUST respond with valid JSON only in this exact format:
{json.dumps(example, indent=2)}

Do not include markdown code blocks, explanations, or any text outside the JSON structure.
Your entire response must be parseable as JSON.
"""
    else:
        json_instruction = """
CRITICAL: You MUST respond with valid JSON only.
Do not include markdown code blocks, explanations, or any text outside the JSON structure.
Your entire response must be parseable as JSON.
"""

    # Find or create system message
    system_idx = next((i for i, m in enumerate(enhanced) if m.type == "system"), None)

    if system_idx is not None:
        # Inject PNL prefix + original content + JSON instructions
        enhanced[system_idx].content = (
            PNL_ANTI_HALLUCINATION_PREFIX +
            "\n\n" +
            "═══════════════════════════════════════════════════════════════════════════\n" +
            "  ORIGINAL INSTRUCTIONS (from LangSmith):\n" +
            "═══════════════════════════════════════════════════════════════════════════\n\n" +
            enhanced[system_idx].content +
            "\n\n" +
            "═══════════════════════════════════════════════════════════════════════════\n" +
            "  JSON RESPONSE FORMAT:\n" +
            "═══════════════════════════════════════════════════════════════════════════\n\n" +
            json_instruction
        )
    else:
        # Create new system message with PNL prefix + JSON instructions
        system_content = (
            PNL_ANTI_HALLUCINATION_PREFIX +
            "\n\n" +
            "═══════════════════════════════════════════════════════════════════════════\n" +
            "  JSON RESPONSE FORMAT:\n" +
            "═══════════════════════════════════════════════════════════════════════════\n\n" +
            json_instruction
        )
        enhanced.insert(0, SystemMessage(content=system_content))

    return enhanced


def _get_type_name(field_type) -> str:
    """Extract simple type name from type annotation.

    Handles:
    - list[str] → "array"
    - str → "string"
    - int → "integer"
    - bool → "boolean"
    - dict → "object"
    """
    import typing

    # Get the origin type (e.g., list from list[str])
    origin = typing.get_origin(field_type)

    if origin is list:
        return "array"
    elif field_type is str or field_type == str:
        return "string"
    elif field_type is int or field_type == int:
        return "integer"
    elif field_type is bool or field_type == bool:
        return "boolean"
    elif field_type is dict or origin is dict:
        return "object"
    else:
        return "string"  # Default fallback


def _generate_example_from_schema(schema: Dict) -> Dict:
    """Generate an example JSON object from a Pydantic schema.

    Args:
        schema: Pydantic schema dictionary

    Returns:
        Example dictionary with placeholder values
    """
    if "properties" not in schema:
        return {}

    example = {}
    for field_name, field_info in schema["properties"].items():
        field_type = field_info.get("type", "string")

        if field_type == "string":
            example[field_name] = f"example_{field_name}"
        elif field_type == "integer":
            example[field_name] = 0
        elif field_type == "number":
            example[field_name] = 0.0
        elif field_type == "boolean":
            example[field_name] = True
        elif field_type == "array":
            # Get item type from schema
            items = field_info.get("items", {})
            item_type = items.get("type", "string")
            if item_type == "string":
                example[field_name] = ["item1", "item2", "item3"]
            else:
                example[field_name] = []
        elif field_type == "object":
            example[field_name] = {}
        else:
            example[field_name] = None

    return example


def extract_json_from_response(content: str) -> str:
    """Extract JSON from response, handling markdown code blocks.

    DeepSeek sometimes wraps JSON in ```json...``` blocks despite instructions.
    This function extracts the JSON content.

    Args:
        content: Response content (may contain markdown)

    Returns:
        Extracted JSON string

    Raises:
        ValueError: If no valid JSON found
    """
    # Try direct parsing first
    try:
        json.loads(content)
        return content
    except json.JSONDecodeError:
        pass

    # Try extracting from ```json ... ``` blocks
    json_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
    if json_match:
        json_str = json_match.group(1).strip()
        try:
            json.loads(json_str)  # Validate
            return json_str
        except json.JSONDecodeError:
            pass

    # Try extracting from generic ``` ... ``` blocks
    code_match = re.search(r'```\s*\n(.*?)\n```', content, re.DOTALL)
    if code_match:
        json_str = code_match.group(1).strip()
        try:
            json.loads(json_str)  # Validate
            return json_str
        except json.JSONDecodeError:
            pass

    # Last resort: look for JSON object patterns
    json_obj_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
    if json_obj_match:
        json_str = json_obj_match.group(0)
        try:
            json.loads(json_str)  # Validate
            return json_str
        except json.JSONDecodeError:
            pass

    raise ValueError(f"No valid JSON found in response: {content[:200]}...")


def load_deepseek_for_structured_output(
    model_name: str,
    schema: Optional[Type[BaseModel]] = None
) -> BaseChatModel:
    """Load DeepSeek model configured for structured output.

    IMPORTANT: This function ALWAYS uses deepseek-reasoner (V3.2-Exp Thinking Mode)
    regardless of the model_name parameter, as per project requirements.

    deepseek-reasoner provides:
    - 8x higher max_tokens (64K vs 8K for deepseek-chat)
    - Superior reasoning capabilities
    - Default 32K output (vs 4K for deepseek-chat)

    This function creates a DeepSeek model with:
    - Explicit response_format={'type': 'json_object'}
    - Enhanced prompting for reliable JSON responses
    - Post-processing to extract JSON from markdown
    - Maximum output length (64K tokens)

    Args:
        model_name: Model identifier (ignored - always uses deepseek-reasoner)
        schema: Optional Pydantic model for response structure

    Returns:
        Configured ChatDeepSeek model with deepseek-reasoner

    Example:
        >>> from pydantic import BaseModel
        >>> class Queries(BaseModel):
        ...     queries: list[str]
        >>> model = load_deepseek_for_structured_output("deepseek/deepseek-chat", Queries)
        >>> # Actually uses deepseek-reasoner internally
        >>> response = model.invoke([{"role": "user", "content": "Generate queries"}])
    """
    # ALWAYS use deepseek-reasoner (project requirement)
    # Reasoning: deepseek-reasoner has 8x higher output limits (64K vs 8K)
    # and superior quality for complex reasoning tasks
    model_id = "deepseek-reasoner"

    # Create base model with JSON mode and maximum output tokens
    model = ChatDeepSeek(
        model=model_id,
        response_format={'type': 'json_object'},  # Critical for DeepSeek
        temperature=0,
        max_tokens=64000  # deepseek-reasoner max (vs 8K for deepseek-chat)
    )

    return model


# Patch for generate_queries in researcher_graph/graph.py
async def generate_queries_deepseek(
    messages: List[Dict],
    model_id: str,
    schema: Type[BaseModel]
) -> Dict:
    """Generate queries using DeepSeek with enhanced structured output support.

    This is a drop-in replacement for the standard generate_queries logic
    when using DeepSeek models.

    Args:
        messages: List of message dictionaries
        model_id: DeepSeek model identifier
        schema: Pydantic schema for response structure

    Returns:
        Parsed response dictionary

    Raises:
        ValueError: If response cannot be parsed as valid JSON
    """
    # Load model with JSON mode
    model = load_deepseek_for_structured_output(model_id, schema)

    # Enhance messages with JSON instructions
    enhanced_messages = enhance_prompt_for_json(
        [SystemMessage(content=m["content"]) if m["role"] == "system"
         else AIMessage(content=m["content"]) if m["role"] == "assistant"
         else BaseMessage(content=m["content"], type=m["role"])
         for m in messages],
        schema=schema
    )

    # Invoke model
    response = await model.ainvoke(enhanced_messages)

    # Extract and parse JSON
    try:
        json_str = extract_json_from_response(response.content)
        parsed = json.loads(json_str)
        return parsed
    except (ValueError, json.JSONDecodeError) as e:
        # Log error and raise with context
        print(f"DeepSeek JSON parsing failed: {e}")
        print(f"Response content (first 500 chars): {response.content[:500]}")
        raise ValueError(f"Failed to parse DeepSeek response as JSON: {e}")
