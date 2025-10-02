# DeepSeek Incompatibility Analysis

**Date**: October 2, 2025
**Models Tested**: `deepseek-reasoner` (DeepSeek-R1), `deepseek-chat` (DeepSeek-V3)
**Backend**: chat-langchain master branch (retrieval_graph)
**Result**: ❌ **INCOMPATIBLE** with current backend implementation

---

## Executive Summary

Both DeepSeek models (`deepseek-reasoner` and `deepseek-chat`) are **incompatible** with the chat-langchain backend's structured output implementation. While the API calls succeed (HTTP 200), the models return empty responses, causing TypeErrors in the `generate_queries` node.

**Root Cause**: DeepSeek requires specific JSON mode configuration (`response_format={'type': 'json_object'}`) that is not provided by LangChain's generic `with_structured_output()` method.

---

## Symptoms

### Test Results (DeepSeek Chat V3)
```json
{
  "model_id": "deepseek/deepseek-chat",
  "total_tests": 3,
  "successful_tests": 3,  // False positive - no errors but empty responses
  "results": [
    {
      "test_id": "test_1_simple",
      "elapsed_time": 10.21,
      "chunk_count": 2,
      "response_length": 0,  // ❌ EMPTY
      "response_full": ""     // ❌ EMPTY
    }
  ]
}
```

### Backend Error Logs
```
[2025-10-02T13:51:08] [error] Run encountered an error in graph:
TypeError: 'NoneType' object is not subscriptable

File "backend/retrieval_graph/researcher_graph/graph.py", line 53
return {"queries": response["queries"]}
       ~~~~~~~~^^^^^^^^^^^

During task with name 'generate_queries'
```

**Pattern**:
1. ✅ API calls succeed (HTTP 200 OK to `https://api.deepseek.com/v1/chat/completions`)
2. ✅ Authentication works (no 401/403 errors)
3. ❌ `response` is `None` when accessing structured output
4. ❌ Final AI responses are empty (0 characters)

---

## Technical Analysis

### Backend Implementation (researcher_graph/graph.py)

```python
# Lines 40-45
structured_output_kwargs = (
    {"method": "function_calling"} if "openai" in configuration.query_model else {}
)
model = load_chat_model(configuration.query_model).with_structured_output(
    Response, **structured_output_kwargs
)
```

**Problem**:
- **OpenAI models** get explicit `method="function_calling"`
- **All other models** (including DeepSeek) get empty kwargs `{}`
- LangChain's `with_structured_output()` defaults to a method that DeepSeek doesn't support properly

### DeepSeek JSON Mode Requirements

According to [DeepSeek API documentation](https://api-docs.deepseek.com/guides/json_mode):

```python
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    response_format={'type': 'json_object'}  # ❌ NOT SET by backend
)
```

**Required Configuration**:
1. ✅ `response_format={'type': 'json_object'}` in API call
2. ✅ Word "json" in system/user prompt
3. ✅ Example JSON structure in prompt

**Known Issue**: DeepSeek documentation states:
> "The API may occasionally return empty content. DeepSeek is actively working to optimize this issue."

This explains the empty responses we're seeing.

---

## Comparison: DeepSeek vs Working Models

| Feature | GPT-5 | Claude Sonnet 4.5 | DeepSeek Chat |
|---------|-------|-------------------|---------------|
| **API Success** | ✅ HTTP 200 | ✅ HTTP 200 | ✅ HTTP 200 |
| **Structured Output** | ✅ Function calling | ✅ Function calling | ❌ Returns None |
| **Response Content** | ✅ 11k-15k chars | ✅ 2k-4k chars | ❌ 0 chars |
| **Backend Compatibility** | ✅ Works | ✅ Works | ❌ Fails |

---

## Failed Attempts

### Attempt 1: DeepSeek Reasoner (deepseek-reasoner)
- **Model**: DeepSeek-R1 (reasoning mode)
- **Result**: Empty responses, TypeError
- **Reason**: Does NOT support structured output at all (per LangChain docs)

### Attempt 2: DeepSeek Chat (deepseek-chat)
- **Model**: DeepSeek-V3 (standard mode)
- **Result**: Empty responses, TypeError
- **Reason**: Supports structured output BUT requires explicit JSON mode config

---

## Why DeepSeek Fails

### 1. Missing JSON Mode Configuration
LangChain's `ChatDeepSeek.with_structured_output()` doesn't automatically add:
```python
response_format={'type': 'json_object'}
```

### 2. Empty Response Bug
DeepSeek has a known issue where JSON mode occasionally returns empty content, especially without proper prompt formatting.

### 3. Backend Assumption
The backend assumes all non-OpenAI models will work with default `with_structured_output()` behavior, which isn't true for DeepSeek.

---

## Solution Options

### Option A: Backend Modification (NOT IN SCOPE)
Modify `backend/retrieval_graph/researcher_graph/graph.py`:

```python
structured_output_kwargs = {}
if "openai" in configuration.query_model:
    structured_output_kwargs = {"method": "function_calling"}
elif "deepseek" in configuration.query_model:
    structured_output_kwargs = {"method": "json_mode"}  # Force JSON mode
```

**Effort**: 2-3 hours (testing + validation)
**Risk**: May break other model integrations
**Status**: Out of scope for benchmarking task

### Option B: Use DeepSeek for Simple Queries Only
DeepSeek works for single-turn, non-structured responses:
- Direct chat (no multi-step research)
- No structured output requirements
- Simple Q&A without tool calling

**Limitation**: Cannot use with current backend's research workflow

### Option C: Wait for DeepSeek Fixes
DeepSeek is "actively working to optimize" the empty content issue.

**Timeline**: Unknown
**Recommendation**: NOT practical for immediate use

---

## Benchmark Conclusion

**DeepSeek Status**: ❌ **EXCLUDED from final comparison**

### Why Excluded:
1. Backend incompatibility (structured output)
2. Empty responses (known DeepSeek bug)
3. Requires code changes out of scope for benchmarking

### Final Benchmark Scope:
- ✅ GPT-5 Full (tested, slow but works)
- ✅ GPT-5 Mini (tested, fast and works)
- ✅ Claude Sonnet 4.5 (tested, fastest)
- ❌ DeepSeek Chat (tested, incompatible)

---

## Recommendations

### For This MCP Server Project:
**Use Claude Sonnet 4.5** as primary model:
- ✅ Fastest (27-40s per question)
- ✅ Fully compatible with backend
- ✅ Excellent quality responses
- ✅ Good token efficiency

**Alternative**: GPT-5 Mini
- ✅ Fast enough (118-161s)
- ✅ Fully compatible
- ✅ Lower cost than GPT-5 Full

### For Future DeepSeek Integration:
1. Wait for LangChain to improve DeepSeek integration
2. OR modify backend to explicitly support DeepSeek JSON mode
3. OR use DeepSeek only for simple, non-structured queries

---

## Test Artifacts

### Logs
- `/tmp/benchmark_deepseek_retry.log` - DeepSeek Chat test output
- `/tmp/langgraph_dev_restart2.log` - Backend errors (13:50:44 - 13:51:20)

### Results Files
- `mcp_server/results/deepseek-reasoner_results.json` - Reasoner test (empty responses)
- `mcp_server/results/deepseek-chat_results.json` - Chat test (empty responses)

### Code
- `mcp_server/benchmark_models.py` - Benchmark script (lines 52-58: DeepSeek config)
- `backend/retrieval_graph/researcher_graph/graph.py` - Backend structured output (lines 40-53)

---

## Appendix: HTTP Success But Empty Content

This is a **known pattern** with DeepSeek JSON mode:

```python
# API call succeeds
response = await deepseek_client.chat.completions.create(...)
# HTTP 200 OK

# But content is empty or None
print(response.choices[0].message.content)  # Output: "" or None
```

**Workarounds** (not implemented here):
1. Retry logic (3 attempts)
2. Fallback to non-JSON mode
3. Explicit JSON format in system prompt
4. Increased `max_tokens` parameter

None of these workarounds are feasible within the current backend architecture without modifications.

---

**Conclusion**: DeepSeek models are **promising but not production-ready** for this specific backend's structured output requirements. Proceed with GPT-5 Mini or Claude Sonnet 4.5 for the MCP server deep mode.
