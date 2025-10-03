# LangGraph 403 Errors - Quick Reference Guide

## TL;DR - Fast Solutions

### Problem: Getting 403 Forbidden errors with `langgraph dev`

**Fastest Solution (Works in 99% of cases):**

Add to your `.env` file:
```bash
LANGSMITH_TRACING=false
```

Then run:
```bash
langgraph dev
```

**Done.** No more 403 errors. All data stays local.

---

## Quick Diagnosis

### What error are you seeing?

| Error Message | Location | Fix |
|---------------|----------|-----|
| `403 Forbidden from api.smith.langchain.com/auth` | Terminal when starting `langgraph dev` | Add `LANGSMITH_TRACING=false` to `.env` |
| `Failed to batch ingest runs: 403` | Runtime logs | Load `.env` before imports OR set `LANGSMITH_TRACING=false` |
| `403 from auth.langchain.com/auth/v1/user` | Browser console (Studio UI) | Try different browser OR use `langgraph dev --tunnel` |
| `License key is not valid` | LangGraph Studio Desktop | Remove `LANGSMITH_API_KEY` from `.env` (let Studio manage it) |

---

## Environment Variables Cheat Sheet

### For `langgraph dev` (Local Development Server)

```bash
# Option 1: NO tracing (fully local, no 403 errors)
LANGSMITH_TRACING=false
LANGGRAPH_CLI_NO_ANALYTICS=1

# Option 2: WITH tracing (requires free LangSmith account)
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_TRACING=true  # or omit (defaults to true)
```

### For General LangChain Code (Not Platform)

```bash
# Different variable name!
LANGCHAIN_TRACING_V2=false  # or true
LANGSMITH_API_KEY=lsv2_pt_...
```

**Common Mistake:** Using `LANGCHAIN_TRACING_V2` with `langgraph dev` doesn't work. Use `LANGSMITH_TRACING` instead.

---

## Three Deployment Approaches

### 1. Local Development (Fastest - 2 minutes)

**What you need:**
- Nothing! Just your code

**Setup:**
```bash
# .env
LANGSMITH_TRACING=false
OPENAI_API_KEY=sk-...
```

```bash
langgraph dev
```

**Pros:** Zero setup, fully local, no external dependencies
**Cons:** No tracing/observability, in-memory only (state lost on restart)

---

### 2. Free LangSmith Tier (Recommended - 5 minutes)

**What you need:**
- Free LangSmith account (5k traces/month)

**Setup:**

1. Sign up: https://smith.langchain.com (free)
2. Get API key: Settings → API Keys
3. Add to `.env`:
```bash
LANGSMITH_API_KEY=lsv2_pt_...
```

```bash
langgraph dev
```

**Pros:** Full observability, trace debugging, still free
**Cons:** 5k trace/month limit, data on LangSmith servers

---

### 3. Self-Hosted Production (Best - 30 minutes)

**What you need:**
- Docker
- PostgreSQL
- Redis
- Free LangSmith key (for licensing, not tracing)

**Setup:**

```bash
# Generate docker-compose.yml
langgraph dockerfile --add-docker-compose

# Build
langgraph build -t my-app

# .env
LANGSMITH_API_KEY=lsv2_pt_...  # For licensing
LANGSMITH_TRACING=false        # Disable tracing
DATABASE_URI=postgresql://...
REDIS_URI=redis://...
OPENAI_API_KEY=sk-...

# Launch
docker compose up -d
```

**Pros:** Production-ready, persistence, no data leaves infrastructure
**Cons:** More complex setup, requires LangSmith key for licensing

---

## Common Mistakes and Fixes

### Mistake 1: Wrong Environment Variable

**Wrong:**
```bash
LANGCHAIN_TRACING_V2=false  # Doesn't work with langgraph dev
```

**Right:**
```bash
LANGSMITH_TRACING=false  # Correct for langgraph dev
```

---

### Mistake 2: Imports Before .env Load

**Wrong:**
```python
# backend/main.py
from langgraph.graph import StateGraph  # ← Imports FIRST
from dotenv import load_dotenv
load_dotenv()  # ← Too late!
```

**Right:**
```python
# backend/main.py
from dotenv import load_dotenv
load_dotenv()  # ← Load .env FIRST

# Now safe to import
from langgraph.graph import StateGraph
```

---

### Mistake 3: DATABASE_URI vs POSTGRES_URI

**Wrong (in docker-compose.yml):**
```yaml
environment:
  - POSTGRES_URI=postgresql://...  # LangGraph doesn't recognize this
```

**Right:**
```yaml
environment:
  - DATABASE_URI=postgresql://...  # Correct variable name
```

---

### Mistake 4: Manual API Key in Studio Desktop .env

**Wrong:**
```bash
# .env (when using LangGraph Studio Desktop)
LANGSMITH_API_KEY=lsv2_pt_...  # Conflicts with Studio's auto-management
```

**Right:**
```bash
# .env (when using LangGraph Studio Desktop)
# DON'T set LANGSMITH_API_KEY - let Studio manage it
OPENAI_API_KEY=sk-...
```

---

## Browser Issues (Studio UI)

### Error: "Failed to fetch" in browser console

**For Brave:**
```
Settings → Shields → Add smith.langchain.com to allowed sites
Settings → Privacy → Disable "Block cross-site cookies" for this site
```

**For Safari:**
```bash
# Safari blocks localhost - use tunnel
langgraph dev --tunnel
```

**For Any Browser:**
```bash
# Bypass Studio UI, use SDK directly
pip install langgraph-sdk
```

```python
from langgraph_sdk import get_client
client = get_client(url="http://localhost:2024")
```

---

## Complete .env Examples

### Example 1: Local Dev (No LangSmith)

```bash
# Disable all external services
LANGSMITH_TRACING=false
LANGGRAPH_CLI_NO_ANALYTICS=1

# Your app variables
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
WEAVIATE_URL=https://...
WEAVIATE_API_KEY=...
```

---

### Example 2: With Free LangSmith

```bash
# Enable tracing (free tier)
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=my-project

# Your app variables
OPENAI_API_KEY=sk-proj-...
```

---

### Example 3: Docker Production

```bash
# docker-compose.yml environment
DATABASE_URI=postgresql://postgres:postgres@postgres:5432/langgraph
REDIS_URI=redis://redis:6379
LANGSMITH_API_KEY=lsv2_pt_...  # For licensing
LANGSMITH_TRACING=false        # Disable tracing
OPENAI_API_KEY=sk-proj-...
```

---

## Testing Your Setup

### Test 1: Server Health

```bash
curl http://localhost:2024/health
# Should return: {"status": "ok"}
```

### Test 2: List Assistants

```bash
curl http://localhost:2024/assistants
# Should return: [...] (your configured graphs)
```

### Test 3: Python Client

```python
from langgraph_sdk import get_client

client = get_client(url="http://localhost:2024")
assistants = await client.assistants.list()
print(assistants)
```

If these work, your setup is correct (regardless of Studio UI status).

---

## When to Use Each Approach

| Use Case | Approach | Why |
|----------|----------|-----|
| Quick testing | Local dev | Fastest, zero setup |
| Learning LangGraph | Free LangSmith | Get observability without cost |
| Debugging complex graphs | Free LangSmith | Trace visibility essential |
| Production deployment | Self-hosted | Data control, persistence |
| Enterprise/internal | Self-hosted | Security, compliance requirements |
| No internet access | 100% offline custom | FastAPI + no LangSmith key |

---

## Alternative: 100% Independent (No LangSmith Key)

If you don't want any LangSmith dependency (even free tier):

### Use LangGraph OSS with FastAPI

```python
# main.py
from fastapi import FastAPI
from langgraph.graph import StateGraph, END

app = FastAPI()
graph = create_your_graph()  # Your LangGraph code

@app.post("/chat")
async def chat(message: str):
    result = await graph.ainvoke({"messages": [message]})
    return result
```

```bash
uvicorn main:app --reload
```

**No LangGraph Platform, No LangSmith key needed.**

---

## Getting Help

### Official Resources
- Documentation: https://langchain-ai.github.io/langgraph/
- GitHub Discussions: https://github.com/langchain-ai/langgraph/discussions
- LangChain Forum: https://forum.langchain.com/

### Common Issues Repositories
- LangGraph: https://github.com/langchain-ai/langgraph/issues
- LangGraph Studio: https://github.com/langchain-ai/langgraph-studio/issues
- LangSmith SDK: https://github.com/langchain-ai/langsmith-sdk/issues

### Search First
Before opening an issue:
1. Search existing GitHub issues/discussions
2. Check this document's detailed version: `LANGGRAPH_DEV_403_ERRORS_RESEARCH.md`
3. Review official documentation updates

---

## Key Takeaways

1. **`LANGSMITH_TRACING=false`** solves 99% of 403 errors
2. Use **`LANGSMITH_TRACING`** (not `LANGCHAIN_TRACING_V2`) with `langgraph dev`
3. Load `.env` **before** importing LangChain modules
4. Studio UI issues don't affect server functionality - use SDK directly
5. Free LangSmith tier (5k traces/month) is sufficient for most development
6. Self-hosting requires LangSmith key for licensing, but tracing can be disabled

---

## Document Info

- **Full Report:** `/Users/stephane/Documents/work/chat-langchain/LANGGRAPH_DEV_403_ERRORS_RESEARCH.md`
- **Created:** October 1, 2025
- **Author:** Stéphane Wootha Richard
- **Coverage:** LangGraph 0.3.x - 0.4.x (2024-2025)

---

**Last Updated:** October 1, 2025
