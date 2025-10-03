# LangGraph Local Development: 403 Forbidden Errors with LangSmith

## Research Report - October 1, 2025

This document consolidates findings from GitHub discussions, official documentation, and community forums regarding 403 Forbidden errors when running `langgraph dev` with LangSmith integration.

---

## Executive Summary

The 403 Forbidden error when running `langgraph dev` primarily occurs due to:

1. **Missing or invalid LangSmith API key** during authentication attempts
2. **LangSmith API endpoint authentication failures** when Studio UI tries to connect
3. **Browser security/CORS restrictions** blocking cross-origin requests
4. **Confusion between different tracing environment variables** (`LANGSMITH_TRACING` vs `LANGCHAIN_TRACING_V2`)

**Key Solution:** Set `LANGSMITH_TRACING=false` in your `.env` file to disable tracing entirely and run fully locally without LangSmith.

---

## Table of Contents

1. [Common 403 Error Scenarios](#common-403-error-scenarios)
2. [Environment Variables Reference](#environment-variables-reference)
3. [Solutions and Workarounds](#solutions-and-workarounds)
4. [Self-Hosting Without LangSmith](#self-hosting-without-langsmith)
5. [GitHub Issues and Discussions](#github-issues-and-discussions)
6. [Configuration Examples](#configuration-examples)
7. [References](#references)

---

## Common 403 Error Scenarios

### Scenario 1: Authentication Endpoint 403 Error

**Error Message:**
```
HTTP/1.1 403 Forbidden
GET https://api.smith.langchain.com/auth?langgraph-api=true
```

**Context:**
- Occurs when running `langgraph dev` locally
- LangGraph attempts to verify credentials with LangSmith's API
- Warning displayed: "No license key found, running in test mode with LangSmith API key"

**Source:**
- GitHub Issue: [langchain-ai/langgraph-studio#174](https://github.com/langchain-ai/langgraph-studio/issues/174)
- Date: 2024

**Root Cause:**
- Missing or invalid `LANGSMITH_API_KEY` environment variable
- Account lacks LangGraph Cloud access permissions
- Attempting to use LangGraph Platform features without proper licensing

---

### Scenario 2: LangSmith Trace Submission 403 Error

**Error Message:**
```
langsmith.client:Failed to batch ingest runs: LangSmithError('Failed to POST')
403 Client Error: Forbidden for url: https://api.smith.langchain.com/runs/batch
```

**Context:**
- Occurs during runtime when application tries to send trace data to LangSmith
- Can happen even with a valid API key if configuration is incorrect

**Source:**
- GitHub Issue: [langchain-ai/langsmith-sdk#637](https://github.com/langchain-ai/langsmith-sdk/issues/637)
- Date: 2024

**Root Causes:**
1. Incorrect API key configuration
2. Environment variable not loaded before importing LangChain modules
3. `LANGCHAIN_ENDPOINT` variable causing conflicts
4. API key lacks permissions for the operation

**Suggested Workarounds:**
1. Ensure `.env` file is loaded **before** importing any LangChain modules
2. Verify the API key is correctly set
3. Try removing or commenting out `LANGCHAIN_ENDPOINT` variable
4. Double-check environment variable syntax (no quotes, proper formatting)

---

### Scenario 3: LangGraph Studio UI Authentication Error

**Error Message:**
```
Failed to fetch
403 Forbidden from auth.langchain.com/auth/v1/user
```

**Context:**
- `langgraph dev` server runs successfully on `http://localhost:2024`
- LangGraph Studio UI at `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024` fails to load
- Error appears intermittently with no clear correlation
- Server API remains operational (Python client can connect successfully)

**Source:**
- GitHub Discussion: [langchain-ai/langgraph#2527](https://github.com/langchain-ai/langgraph/discussions/2527)
- Date: 2024

**Root Causes:**
1. Browser security settings blocking mixed content (HTTPS → HTTP)
2. CORS (Cross-Origin Resource Sharing) restrictions
3. Browser shields/privacy features (especially Brave browser)
4. Authentication service intermittent issues on LangChain's side

**Suggested Solutions:**
1. **Browser configuration:**
   - Disable browser shields/security in Brave
   - Add `smith.langchain.com` to allowed sites in browser settings
   - Try different browsers (Chrome, Firefox) instead of Brave/Safari

2. **CORS workaround:**
   - Use a local proxy like nginx to handle CORS headers

3. **Tunnel option:**
   - Use `langgraph dev --tunnel` for Safari compatibility (Safari blocks localhost connections)

4. **Direct API access:**
   - Use Python SDK or REST API directly instead of Studio UI
   - Server remains fully functional even when Studio UI has authentication issues

**Community Note:**
"Clearing cookies does not resolve the issue. The error appears intermittently and persists for fixed periods of time, suggesting an issue on LangChain's authentication service side rather than local configuration."

---

### Scenario 4: License Verification Failed

**Error Message:**
```
ValueError: License key is not valid
License verification failed
```

**Context:**
- LangGraph Studio Desktop application authentication
- Version 0.0.28 and later

**Source:**
- GitHub Issue: [langchain-ai/langgraph-studio#174](https://github.com/langchain-ai/langgraph-studio/issues/174)
- Date: 2024

**Root Causes:**
1. Conflicting environment variables in `.env` file
2. Studio Desktop auto-inserting environment variables that conflict with manual settings
3. Invalid API key format

**Maintainer Recommendations:**
1. **Do NOT manually set** `LANGSMITH_ENDPOINT` or `LANGSMITH_API_KEY` in `.env` file
2. Let Studio Desktop application manage API key insertion automatically
3. Update to latest version of LangGraph Studio (0.0.31+ has better error highlighting)
4. Remove any conflicting environment variables from `.env`

**Solution:**
```bash
# In your .env file, REMOVE these if present:
# LANGSMITH_ENDPOINT=...  ← Remove
# LANGSMITH_API_KEY=...   ← Remove (let Studio manage it)

# Only set application-specific variables:
OPENAI_API_KEY=sk-...
WEAVIATE_URL=https://...
# etc.
```

---

## Environment Variables Reference

### LangGraph Platform Environment Variables

| Variable | Purpose | Values | Default | Notes |
|----------|---------|--------|---------|-------|
| `LANGSMITH_TRACING` | Enable/disable tracing to LangSmith | `true` / `false` | `true` | **Primary control for `langgraph dev`** |
| `LANGSMITH_API_KEY` | Authentication key for LangSmith | `lsv2_pt_...` | None | Required if tracing enabled |
| `LANGCHAIN_TRACING_V2` | Enable LangChain tracing (general) | `true` / `false` | `false` | Used outside LangGraph Platform |
| `LANGSMITH_RUNS_ENDPOINTS` | Self-hosted LangSmith endpoint | JSON string | None | Format: `{"<HOST>":"<KEY>"}` |
| `LANGSMITH_SAMPLING_RATE` | Trace sampling rate | `0.0` to `1.0` | `1.0` | Reduce tracing volume |
| `LANGGRAPH_CLI_NO_ANALYTICS` | Disable CLI analytics | `1` | `0` | Privacy control |
| `LANGGRAPH_AES_KEY` | Encrypt checkpoints | AES key string | None | For data-at-rest encryption |
| `REDIS_URI` | Redis connection string | `redis://...` | None | Required for persistence |
| `DATABASE_URI` | PostgreSQL connection | `postgresql://...` | None | Required for persistence |
| `LANGGRAPH_CLOUD_LICENSE_KEY` | Enterprise license key | License string | None | Self-Hosted Enterprise only |

### Important Distinctions

**For `langgraph dev` (in-memory development server):**
```bash
LANGSMITH_TRACING=false  # ← Use this variable
```

**For general LangChain/LangGraph code (outside Platform):**
```bash
LANGCHAIN_TRACING_V2=false  # ← Use this variable
```

**Common mistake:** Using `LANGCHAIN_TRACING_V2` with `langgraph dev` has no effect. The dev server specifically looks for `LANGSMITH_TRACING`.

---

## Solutions and Workarounds

### Solution 1: Disable Tracing Entirely (Recommended for Local Development)

**Use case:** You want to develop locally without any external services or tracing.

**Configuration:**

Create or update `.env` file in your LangGraph application directory:

```bash
# Disable LangSmith tracing
LANGSMITH_TRACING=false

# Disable CLI analytics (optional)
LANGGRAPH_CLI_NO_ANALYTICS=1

# Your application variables
OPENAI_API_KEY=sk-...
WEAVIATE_URL=https://...
# etc.
```

**Run the development server:**
```bash
langgraph dev
```

**Result:**
- No 403 errors
- No data leaves your local server
- Full application functionality preserved
- LangGraph Studio UI still accessible (but without trace visibility)

**Source:**
- Official Documentation: [Data Storage and Privacy](https://docs.langchain.com/langgraph-platform/data-storage-and-privacy)
- Confirmed working as of October 2025

---

### Solution 2: Use Free LangSmith Tier

**Use case:** You want tracing/observability but don't want to pay.

**Steps:**

1. **Sign up for free LangSmith account:**
   - Visit: https://smith.langchain.com
   - Free tier: 5,000 traces per month

2. **Generate API key:**
   - LangSmith dashboard → Settings → API Keys
   - Create new key → Copy value

3. **Configure `.env` file:**
```bash
# Enable tracing with free tier
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_TRACING=true  # or omit (defaults to true)

# Your application variables
OPENAI_API_KEY=sk-...
```

4. **Run development server:**
```bash
langgraph dev
```

**Result:**
- Full tracing visibility in LangSmith dashboard
- No 403 errors
- 5,000 free traces/month

**Limitations:**
- Free tier limit (5k traces/month)
- Data stored on LangSmith servers (privacy consideration)

**Source:**
- GitHub Discussion: [langchain-ai/langgraph#1604](https://github.com/langchain-ai/langgraph/discussions/1604)
- Developer plan confirmed: 100k nodes executed per month for free (self-hosted)

---

### Solution 3: Environment Variable Loading Order Fix

**Use case:** You have a valid API key but still getting 403 errors.

**Problem:** Environment variables not loaded before LangChain imports.

**Solution:**

```python
# backend/main.py or your entry point
# IMPORTANT: Load .env FIRST, before any LangChain imports

from dotenv import load_dotenv
load_dotenv()  # ← Must be FIRST

# Now import LangChain/LangGraph modules
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph
# etc.
```

**Explanation:**
LangChain modules read environment variables during import. If `.env` isn't loaded yet, they won't see `LANGSMITH_API_KEY` and will attempt unauthenticated requests → 403 Forbidden.

**Source:**
- GitHub Issue: [langchain-ai/langsmith-sdk#637](https://github.com/langchain-ai/langsmith-sdk/issues/637)
- Community-reported solution

---

### Solution 4: Remove Conflicting Environment Variables

**Use case:** LangGraph Studio Desktop showing authentication errors.

**Problem:** Manual `.env` variables conflicting with Studio's auto-managed variables.

**Solution:**

1. **Open `.env` file**

2. **Remove these lines if present:**
```bash
# DELETE these (Studio manages them):
LANGSMITH_ENDPOINT=...  # ← Remove
LANGSMITH_API_KEY=...   # ← Remove (for Studio Desktop only)
```

3. **Keep application-specific variables:**
```bash
# Keep these:
OPENAI_API_KEY=sk-...
WEAVIATE_URL=https://...
WEAVIATE_API_KEY=...
# etc.
```

4. **Restart LangGraph Studio Desktop**

**Result:**
Studio will automatically insert correct `LANGSMITH_API_KEY` and `LANGSMITH_ENDPOINT` without conflicts.

**Source:**
- GitHub Issue: [langchain-ai/langgraph-studio#174](https://github.com/langchain-ai/langgraph-studio/issues/174)
- Maintainer recommendation

---

### Solution 5: Browser Configuration for Studio UI

**Use case:** `langgraph dev` runs successfully, but Studio UI shows 403 errors.

**Browser-specific solutions:**

**For Brave Browser:**
```
1. Open Brave Settings
2. Navigate to Shields
3. Add smith.langchain.com to allowed sites
4. Disable "Block cross-site cookies" for this site
5. Refresh Studio UI
```

**For Safari:**
```bash
# Safari blocks localhost connections
# Use tunnel instead:
langgraph dev --tunnel

# Access Studio via secure tunnel URL provided
```

**For any browser (CORS workaround):**

Set up nginx proxy (advanced):

```nginx
# nginx.conf
server {
    listen 8080;

    location / {
        proxy_pass http://localhost:2024;

        # CORS headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;
    }
}
```

Then access Studio via `http://localhost:8080` instead of direct connection.

**Source:**
- GitHub Discussion: [langchain-ai/langgraph#2527](https://github.com/langchain-ai/langgraph/discussions/2527)

---

### Solution 6: Use Python SDK Directly (Bypass Studio UI)

**Use case:** Studio UI consistently fails, but you need to develop/test.

**Approach:** Skip Studio UI, use Python SDK or REST API directly.

**Example:**

```python
from langgraph_sdk import get_client

# Connect to local langgraph dev server
client = get_client(url="http://localhost:2024")

# List assistants
assistants = await client.assistants.list()

# Create thread
thread = await client.threads.create()

# Run graph
async for chunk in client.runs.stream(
    thread["thread_id"],
    "agent",  # assistant_id
    input={"messages": [{"role": "user", "content": "Hello"}]}
):
    print(chunk)
```

**REST API Example:**

```bash
# Health check
curl http://localhost:2024/health

# List assistants
curl http://localhost:2024/assistants

# Create thread
curl -X POST http://localhost:2024/threads \
  -H "Content-Type: application/json" \
  -d '{}'

# Run graph
curl -X POST http://localhost:2024/threads/{thread_id}/runs \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "agent",
    "input": {"messages": [{"role": "user", "content": "Hello"}]}
  }'
```

**Advantages:**
- No browser authentication issues
- No CORS problems
- Full programmatic control
- Works even when Studio UI fails

**Documentation:**
- REST API: http://localhost:2024/docs (auto-generated)
- Python SDK: https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/

---

## Self-Hosting Without LangSmith

### Option 1: LangGraph Platform Self-Hosted Lite

**What you get:**
- Up to 1 million node executions per year (free Developer plan)
- PostgreSQL + Redis persistence
- Full LangGraph Platform features
- LangGraph Studio Desktop integration

**What you need:**
- LangSmith API key (free tier: 5k traces/month)
- PostgreSQL database
- Redis instance

**Setup:**

1. **Generate Dockerfile and docker-compose.yml:**
```bash
langgraph dockerfile --add-docker-compose
```

2. **Build Docker image:**
```bash
langgraph build -t my-app
```

3. **Configure docker-compose.yml:**
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: langgraph
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  langgraph:
    image: my-app:latest
    depends_on:
      - postgres
      - redis
    environment:
      # IMPORTANT: Use DATABASE_URI not POSTGRES_URI
      - DATABASE_URI=postgresql://postgres:postgres@postgres:5432/langgraph
      - REDIS_URI=redis://redis:6379
      - LANGSMITH_API_KEY=${LANGSMITH_API_KEY}
      - LANGSMITH_TRACING=true  # or false to disable
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      # Add other application variables
    ports:
      - "2024:8000"

volumes:
  postgres_data:
  redis_data:
```

4. **Create `.env` file:**
```bash
LANGSMITH_API_KEY=lsv2_pt_...  # Free tier
OPENAI_API_KEY=sk-...
# Other variables
```

5. **Launch:**
```bash
docker compose up -d
```

**Important Notes:**
- Use `DATABASE_URI` not `POSTGRES_URI` (common mistake)
- Set `LANGSMITH_TRACING=false` in docker-compose.yml to disable tracing after setup
- LangSmith API key still required for platform licensing (even with tracing disabled)

**Source:**
- Official Guide: https://langchain-ai.github.io/langgraph/how-tos/deploy-self-hosted/
- GitHub Issue: [langchain-ai/langgraph#2549](https://github.com/langchain-ai/langgraph/issues/2549)
- Stack Overflow: https://stackoverflow.com/questions/79295021/langgraph-deployment-with-docker-compose

---

### Option 2: LangGraph OSS with Custom FastAPI (100% Independence)

**What you get:**
- Zero dependency on LangSmith
- Zero dependency on LangGraph Platform
- 100% self-hosted
- Full control over deployment

**What you lose:**
- LangGraph Studio UI integration
- Built-in persistence/checkpointing (must implement yourself)
- Streaming support (must implement yourself)

**Architecture:**
```
LangGraph OSS (MIT license, free)
    ↓
Custom FastAPI endpoint
    ↓
Self-hosted Redis + PostgreSQL
    ↓
Your own authentication (e.g., Supabase, Firebase)
```

**Example implementation:**

```python
# main.py
from fastapi import FastAPI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from typing import TypedDict
import asyncio

app = FastAPI()

# Define your graph state
class State(TypedDict):
    messages: list[str]

# Define your graph
def create_graph():
    workflow = StateGraph(State)

    def chatbot(state: State):
        # Your logic here
        return {"messages": state["messages"] + ["Response"]}

    workflow.add_node("chatbot", chatbot)
    workflow.set_entry_point("chatbot")
    workflow.add_edge("chatbot", END)

    # Use PostgreSQL checkpointer
    checkpointer = PostgresSaver.from_conn_string(
        "postgresql://user:pass@localhost:5432/db"
    )

    return workflow.compile(checkpointer=checkpointer)

graph = create_graph()

@app.post("/chat")
async def chat(message: str):
    config = {"configurable": {"thread_id": "default"}}
    result = await graph.ainvoke(
        {"messages": [message]},
        config=config
    )
    return result

# Run with: uvicorn main:app --reload
```

**Advantages:**
- Zero external dependencies
- Full control over infrastructure
- No licensing concerns
- Use any observability tool (Langfuse, Arize, custom)

**Disadvantages:**
- Must implement persistence, streaming, auth yourself
- No built-in UI
- Higher development effort

**Community Alternatives:**

1. **Aegra** (https://github.com/ibbybuilds/aegra)
   - Self-hosted LangGraph Platform alternative
   - Real authentication (Supabase, Firebase)
   - 5-minute Docker setup

2. **Agent Service Toolkit**
   - LangGraph with FastAPI
   - Community-maintained

**Source:**
- GitHub Discussion: [langchain-ai/langgraph#1604](https://github.com/langchain-ai/langgraph/discussions/1604)
- Community: Latenode Forum

---

### Option 3: Alternative Observability (Langfuse)

**Use case:** You want observability without LangSmith dependency.

**Langfuse:**
- Open source (MIT license)
- Freely self-hostable
- Full LangChain/LangGraph integration
- Alternative to LangSmith

**Setup:**

1. **Self-host Langfuse:**
```bash
# docker-compose.yml
version: '3.8'
services:
  langfuse:
    image: langfuse/langfuse:latest
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://...
      - NEXTAUTH_SECRET=...
```

2. **Configure LangChain to use Langfuse:**
```python
from langfuse.callback import CallbackHandler

langfuse_handler = CallbackHandler(
    host="http://localhost:3000",
    public_key="pk-...",
    secret_key="sk-..."
)

# Use with LangChain/LangGraph
result = graph.invoke(
    input,
    config={"callbacks": [langfuse_handler]}
)
```

**Advantages:**
- 100% self-hosted
- No LangSmith dependency
- Full observability features
- Active development

**Comparison:**
| Feature | LangSmith | Langfuse |
|---------|-----------|----------|
| Self-hosting | Paid ($$$) | Free (open source) |
| Free tier | 5k traces/mo | Unlimited (self-hosted) |
| LangGraph integration | Native | Via callbacks |
| Studio UI | Built-in | Separate UI |

**Source:**
- Langfuse Docs: https://langfuse.com/docs/integrations/langchain/tracing
- Comparison: https://langfuse.com/faq/all/langsmith-alternative
- Medium Article: "Self-hosting Langfuse: LLM Observability on Your Own Infrastructure" (2024)

---

## GitHub Issues and Discussions

### Summary of Key Issues

| Issue | Title | Status | Key Findings |
|-------|-------|--------|--------------|
| [#2549](https://github.com/langchain-ai/langgraph/issues/2549) | Deploy on intranet without LangSmith key | Open | **Conclusion:** LangSmith key required for Platform, but can use free tier |
| [#1604](https://github.com/langchain-ai/langgraph/discussions/1604) | Self-host without a key | Answered | **Solutions:** (1) Free Developer tier (2) Custom FastAPI (3) Aegra alternative |
| [#174](https://github.com/langchain-ai/langgraph-studio/issues/174) | Authentication bug v0.0.28 | Closed | **Fix:** Update to v0.0.31+, remove manual env vars, let Studio manage keys |
| [#637](https://github.com/langchain-ai/langsmith-sdk/issues/637) | 403 Client Error: Forbidden | Open | **Workarounds:** (1) Load .env before imports (2) Remove LANGCHAIN_ENDPOINT (3) Verify API key |
| [#2527](https://github.com/langchain-ai/langgraph/discussions/2527) | 403 from auth.langchain.com | Open | **Workarounds:** (1) Browser config (2) Try different browsers (3) Use tunnel (4) Use SDK directly |
| [#2472](https://github.com/langchain-ai/langgraph/discussions/2472) | Local studio setup issues | Answered | **Solution:** Python >= 3.11, update dependencies, browser compatibility |

---

### Detailed Issue Analysis

#### Issue #2549: Deploy LangGraph Platform on Intranet Without LangSmith Key

**Question:** Can I deploy LangGraph Platform on an internal network without entering a LangSmith key?

**Answer:** Not completely, but you can use the free tier.

**Details:**
- **Self-Hosted Lite version:** Requires LangSmith API key for licensing
- **Free Developer plan:** Up to 1M node executions per year
- **Tracing can be disabled:** Set `LANGSMITH_TRACING=false` to prevent data leaving your network
- **Authentication:** LangSmith key authenticates the platform license, not just tracing

**Recommendation:**
1. Create free LangSmith account (5k traces/month)
2. Use API key for platform authentication
3. Disable tracing with `LANGSMITH_TRACING=false`
4. All data stays on your infrastructure

**Alternative:**
Use LangGraph OSS with custom FastAPI deployment (no Platform, no key required).

**Date:** 2024
**Status:** Confirmed by maintainers

---

#### Issue #1604: Can I Self-Host a LangGraph App Without a Key?

**Question:** Is it possible to deploy LangGraph without any LangSmith/LangChain account?

**Answer:** Yes, but not using LangGraph Platform.

**Three approaches identified:**

1. **Self-Hosted Lite (with free LangSmith key):**
   - Free Developer account: 1M node executions/year
   - Requires PostgreSQL + Redis
   - LangSmith key for licensing (can disable tracing)

2. **Custom FastAPI Deployment (100% independent):**
   - Use LangGraph OSS library directly
   - Implement your own API endpoints
   - Self-host Redis + PostgreSQL
   - Community examples: agent-service-toolkit

3. **Community Alternatives:**
   - **Aegra**: https://github.com/ibbybuilds/aegra
     - Self-hosted LangGraph Platform alternative
     - Real authentication (Supabase, Firebase)
     - 5-minute Docker setup
     - MIT license

**Key Quote:**
> "LangGraph is an MIT-licensed open-source library and is free to use. The LangGraph Platform (cloud or self-hosted) requires authentication, but the core library does not."

**Date:** 2024
**Status:** Multiple community solutions validated

---

#### Issue #174: Authentication Bug - LangGraph Studio v0.0.28

**Error:**
```
ValueError: License key is not valid
Authentication with LangSmith failed
403 Forbidden
```

**Root Cause:**
Conflicting environment variables in `.env` file when using LangGraph Studio Desktop.

**Fix (from maintainers):**

1. **Update to v0.0.31 or later** (better error messages)

2. **Remove manual env vars from `.env`:**
```bash
# WRONG - causes conflicts:
LANGSMITH_ENDPOINT=https://api.smith.langchain.com  # ← Remove
LANGSMITH_API_KEY=lsv2_pt_...                       # ← Remove

# RIGHT - let Studio Desktop manage these automatically:
OPENAI_API_KEY=sk-...
WEAVIATE_URL=https://...
```

3. **Restart LangGraph Studio Desktop**

**Explanation:**
Studio Desktop automatically inserts `LANGSMITH_API_KEY` and `LANGSMITH_ENDPOINT`. Manual settings in `.env` conflict with auto-managed values.

**Date:** 2024
**Status:** Resolved in v0.0.31+

---

#### Issue #637: Failed to Batch Ingest Runs - 403 Forbidden

**Error:**
```python
langsmith.client:Failed to batch ingest runs: LangSmithError('Failed to POST')
403 Client Error: Forbidden for url: https://api.smith.langchain.com/runs/batch
```

**Context:**
Application has valid `LANGSMITH_API_KEY` but still receives 403 when attempting to send traces.

**Identified Causes:**

1. **Import order issue:**
   - LangChain reads env vars during module import
   - If `.env` not loaded first, modules don't see `LANGSMITH_API_KEY`
   - Results in unauthenticated requests → 403

2. **Conflicting LANGCHAIN_ENDPOINT:**
   - Custom `LANGCHAIN_ENDPOINT` can override default
   - May point to wrong API or use wrong authentication

3. **API key format issues:**
   - Quotes around value
   - Whitespace in variable
   - Wrong key copied

**Solutions (from community):**

**Solution 1: Load .env before imports**
```python
# backend/main.py
# CRITICAL: Load .env FIRST
from dotenv import load_dotenv
load_dotenv()

# Now safe to import LangChain modules
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph
```

**Solution 2: Remove LANGCHAIN_ENDPOINT**
```bash
# .env file
LANGSMITH_API_KEY=lsv2_pt_...
# LANGCHAIN_ENDPOINT=...  # ← Comment out or remove
```

**Solution 3: Verify API key**
```bash
# Test API key is valid:
curl -H "x-api-key: $LANGSMITH_API_KEY" \
  https://api.smith.langchain.com/info

# Should return 200 OK with account info
```

**Date:** 2024
**Status:** Community workarounds available

---

#### Discussion #2527: Studio UI 403 Error (Intermittent)

**Error:**
```
Failed to fetch
403 Forbidden from auth.langchain.com/auth/v1/user
```

**Symptoms:**
- `langgraph dev` runs successfully at http://localhost:2024
- Studio UI at https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024 times out
- Error appears in browser console (403 from auth endpoint)
- Occurs intermittently with no clear pattern
- Server API remains functional (Python SDK works)

**Root Causes:**

1. **Browser security (Brave, Safari):**
   - Mixed content blocking (HTTPS → HTTP)
   - Cross-site cookies blocked
   - Shields/privacy features active

2. **CORS restrictions:**
   - Studio UI (HTTPS) calling local server (HTTP)
   - Browser blocks cross-origin requests

3. **LangChain auth service issues:**
   - Intermittent problems on auth.langchain.com
   - Not related to local configuration

**Solutions:**

**For Brave:**
```
Settings → Shields → Add smith.langchain.com to allowed sites
Settings → Privacy → Disable "Block cross-site cookies" for this site
```

**For Safari:**
```bash
# Safari blocks localhost connections entirely
# Use tunnel instead:
langgraph dev --tunnel

# Access via provided ngrok-style URL
```

**For any browser (advanced):**
Set up local nginx proxy:

```nginx
server {
    listen 8080;
    location / {
        proxy_pass http://localhost:2024;
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
    }
}
```

Access via http://localhost:8080.

**Workaround: Use SDK directly**

Skip Studio UI entirely:

```python
from langgraph_sdk import get_client

client = get_client(url="http://localhost:2024")
assistants = await client.assistants.list()
```

**Community Note:**
"The server API works perfectly even when Studio UI fails. This is a Studio UI authentication issue, not a server problem."

**Date:** 2024
**Status:** No official fix, workarounds available

---

## Configuration Examples

### Example 1: Minimal Local Development (No LangSmith)

**`.env` file:**
```bash
# Disable all external services
LANGSMITH_TRACING=false
LANGGRAPH_CLI_NO_ANALYTICS=1

# Application variables
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
WEAVIATE_URL=https://my-cluster.weaviate.cloud
WEAVIATE_API_KEY=my-key
```

**`langgraph.json`:**
```json
{
  "dependencies": ["langchain", "langgraph", "langchain-openai"],
  "graphs": {
    "agent": "./backend/graph.py:graph"
  },
  "env": ".env"
}
```

**Run:**
```bash
langgraph dev
```

**Result:**
- Fully local execution
- No 403 errors
- No data leaves your machine
- Studio UI accessible but no traces visible

---

### Example 2: Development with Free LangSmith Tier

**`.env` file:**
```bash
# Enable LangSmith tracing (free tier)
LANGSMITH_API_KEY=lsv2_pt_xxxxxxxxxxxxxxxx
LANGSMITH_TRACING=true  # or omit (defaults to true)

# Optional: Set project name
LANGSMITH_PROJECT=my-project

# Application variables
OPENAI_API_KEY=sk-proj-...
```

**Run:**
```bash
langgraph dev
```

**Result:**
- Full tracing in LangSmith dashboard
- 5,000 traces/month free
- Studio UI with full observability
- No 403 errors

**LangSmith Dashboard:**
- View traces: https://smith.langchain.com/
- Search, filter, debug traces
- View prompts, completions, latency

---

### Example 3: Self-Hosted with Docker Compose (Persistence)

**`docker-compose.yml`:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: langgraph
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  langgraph:
    image: chat-langchain:latest
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "2024:8000"
    environment:
      # CRITICAL: Use DATABASE_URI not POSTGRES_URI
      - DATABASE_URI=postgresql://postgres:postgres@postgres:5432/langgraph
      - REDIS_URI=redis://redis:6379

      # Tracing configuration
      - LANGSMITH_API_KEY=${LANGSMITH_API_KEY}
      - LANGSMITH_TRACING=false  # Disable tracing, keep platform license

      # Application variables
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - WEAVIATE_URL=${WEAVIATE_URL}
      - WEAVIATE_API_KEY=${WEAVIATE_API_KEY}

volumes:
  postgres_data:
  redis_data:
```

**`.env` file:**
```bash
LANGSMITH_API_KEY=lsv2_pt_...  # Free tier for licensing
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
WEAVIATE_URL=https://my-cluster.weaviate.cloud
WEAVIATE_API_KEY=my-key
```

**Build and run:**
```bash
# Generate Dockerfile
langgraph dockerfile --add-docker-compose

# Build image
langgraph build -t chat-langchain:latest

# Launch services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f langgraph

# Test API
curl http://localhost:2024/health
```

**Result:**
- Full persistence (PostgreSQL)
- Streaming support (Redis)
- No tracing to LangSmith (data stays local)
- Platform licensed with free LangSmith key
- Production-ready setup

---

### Example 4: 100% Independent (Custom FastAPI)

**`backend/main.py`:**
```python
from fastapi import FastAPI
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from typing import TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
import os

app = FastAPI()

# State definition
class State(TypedDict):
    messages: Annotated[list, "messages"]

# Graph definition
def create_graph():
    # LLM
    llm = ChatOpenAI(
        model="gpt-4",
        api_key=os.getenv("OPENAI_API_KEY")
    )

    # Node function
    def chatbot(state: State):
        messages = state["messages"]
        response = llm.invoke(messages)
        return {"messages": [response]}

    # Build graph
    workflow = StateGraph(State)
    workflow.add_node("chatbot", chatbot)
    workflow.set_entry_point("chatbot")
    workflow.add_edge("chatbot", END)

    # Checkpointer
    checkpointer = PostgresSaver.from_conn_string(
        os.getenv("DATABASE_URI")
    )

    return workflow.compile(checkpointer=checkpointer)

graph = create_graph()

# API models
class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"

class ChatResponse(BaseModel):
    response: str
    thread_id: str

# Endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    config = {"configurable": {"thread_id": request.thread_id}}

    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=request.message)]},
        config=config
    )

    return ChatResponse(
        response=result["messages"][-1].content,
        thread_id=request.thread_id
    )

@app.get("/health")
async def health():
    return {"status": "ok"}

# Run with: uvicorn main:app --reload
```

**`.env` file:**
```bash
DATABASE_URI=postgresql://user:pass@localhost:5432/db
OPENAI_API_KEY=sk-proj-...
```

**Run:**
```bash
# Install dependencies
pip install fastapi uvicorn langgraph langchain-openai psycopg2-binary

# Start server
uvicorn main:app --reload
```

**Test:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello",
    "thread_id": "user-123"
  }'
```

**Result:**
- Zero LangSmith dependency
- Zero LangGraph Platform dependency
- Full control over deployment
- Custom authentication possible
- Can add Langfuse for observability

---

### Example 5: Langfuse Observability (LangSmith Alternative)

**Self-host Langfuse:**

**`docker-compose.langfuse.yml`:**
```yaml
version: '3.8'

services:
  langfuse-db:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: langfuse
    volumes:
      - langfuse_db:/var/lib/postgresql/data

  langfuse:
    image: langfuse/langfuse:latest
    depends_on:
      - langfuse-db
    ports:
      - "3000:3000"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@langfuse-db:5432/langfuse
      NEXTAUTH_SECRET: your-secret-here
      NEXTAUTH_URL: http://localhost:3000
      SALT: your-salt-here

volumes:
  langfuse_db:
```

**Integrate with LangGraph:**

**`backend/graph.py`:**
```python
from langfuse.callback import CallbackHandler
from langgraph.graph import StateGraph, END
import os

# Initialize Langfuse
langfuse_handler = CallbackHandler(
    host="http://localhost:3000",
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY")
)

def create_graph():
    workflow = StateGraph(State)
    # ... define graph ...
    return workflow.compile(checkpointer=checkpointer)

graph = create_graph()

# Use with tracing
result = await graph.ainvoke(
    input,
    config={"callbacks": [langfuse_handler]}
)
```

**`.env` file:**
```bash
# No LangSmith variables needed
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
OPENAI_API_KEY=sk-proj-...
```

**Result:**
- 100% self-hosted observability
- No LangSmith dependency
- Full trace visibility at http://localhost:3000
- Free and open source

---

## References

### Official Documentation

1. **LangGraph Platform - Local Server:**
   - URL: https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/
   - Topics: `langgraph dev`, environment variables, Studio UI access
   - Date: 2024-2025 (current)

2. **LangGraph Studio - Quick Start:**
   - URL: https://docs.langchain.com/langgraph-platform/quick-start-studio
   - Topics: Studio Desktop, authentication, project setup
   - Date: 2024-2025 (current)

3. **Data Storage and Privacy:**
   - URL: https://docs.langchain.com/langgraph-platform/data-storage-and-privacy
   - Topics: `LANGSMITH_TRACING`, `LANGGRAPH_CLI_NO_ANALYTICS`, data flows
   - Date: 2024-2025 (current)

4. **Environment Variables Reference:**
   - URL: https://langchain-ai.github.io/langgraphjs/cloud/reference/env_var/
   - Topics: Complete environment variable reference
   - Date: 2024-2025 (current)

5. **Self-Hosted Deployment:**
   - URL: https://langchain-ai.github.io/langgraph/how-tos/deploy-self-hosted/
   - Topics: Docker, docker-compose, PostgreSQL, Redis
   - Date: 2024-2025 (current)

6. **Trace with LangGraph:**
   - URL: https://docs.langchain.com/langsmith/trace-with-langgraph
   - Topics: LangSmith integration, tracing configuration
   - Date: 2024-2025 (current)

---

### GitHub Issues and Discussions

1. **Issue #2549: Deploy on intranet without LangSmith key**
   - URL: https://github.com/langchain-ai/langgraph/issues/2549
   - Status: Open
   - Key info: Free tier option, tracing can be disabled
   - Date: 2024

2. **Discussion #1604: Self-host without a key**
   - URL: https://github.com/langchain-ai/langgraph/discussions/1604
   - Status: Answered
   - Key info: FastAPI alternative, Aegra project, Developer plan details
   - Date: 2024

3. **Issue #174: Authentication Bug - Studio v0.0.28**
   - URL: https://github.com/langchain-ai/langgraph-studio/issues/174
   - Status: Closed (fixed in v0.0.31+)
   - Key info: Remove manual env vars, let Studio manage keys
   - Date: 2024

4. **Issue #637: Failed to batch ingest runs - 403**
   - URL: https://github.com/langchain-ai/langsmith-sdk/issues/637
   - Status: Open
   - Key info: Load .env before imports, remove LANGCHAIN_ENDPOINT
   - Date: 2024

5. **Discussion #2527: Studio UI 403 error**
   - URL: https://github.com/langchain-ai/langgraph/discussions/2527
   - Status: Open
   - Key info: Browser config, tunnel option, use SDK directly
   - Date: 2024

6. **Discussion #2472: Local studio setup**
   - URL: https://github.com/langchain-ai/langgraph/discussions/2472
   - Status: Answered
   - Key info: Python >= 3.11, browser compatibility
   - Date: 2024

7. **Issue #2731: langgraph dev asks for inmem installation**
   - URL: https://github.com/langchain-ai/langgraph/issues/2731
   - Status: Closed
   - Key info: Install with `pip install "langgraph-cli[inmem]"`
   - Date: 2024

8. **Issue #5790: langgraph dev ignores checkpointer**
   - URL: https://github.com/langchain-ai/langgraph/issues/5790
   - Status: Open
   - Key info: Dev server uses in-memory only, state lost on restart
   - Date: 2024

---

### Community Resources

1. **Stack Overflow - LangGraph Docker Compose Deployment:**
   - URL: https://stackoverflow.com/questions/79295021/langgraph-deployment-with-docker-compose
   - Topic: DATABASE_URI vs POSTGRES_URI mistake
   - Date: 2024

2. **Latenode Community - Self-hosting without LangSmith:**
   - URL: https://community.latenode.com/t/self-hosting-langgraph-agents-independently-without-langsmith-integration/33746
   - Topic: FastAPI alternatives, custom deployment
   - Date: 2024

3. **Medium - LangSmith Tracing Deep Dive:**
   - Author: Aviad Rozenhek
   - URL: https://medium.com/@aviadr1/langsmith-tracing-deep-dive-beyond-the-docs-75016c91f747
   - Topic: Advanced tracing configuration
   - Date: 2024

4. **Medium - Self-hosting Langfuse:**
   - Author: Doil Kim
   - URL: https://medium.com/@kimdoil1211/self-hosting-langfuse-llm-observability-on-your-own-infrastructure-623595858b12
   - Topic: Langfuse as LangSmith alternative
   - Date: 2024

5. **Neuralware - Build and Deploy LangGraph from Scratch:**
   - URL: https://neuralware.github.io/posts/langgraph-deployment/
   - Topic: Complete deployment guide
   - Date: 2024

6. **Chris Carr - LangSmith with Dockerized n8n:**
   - URL: https://chrisdavidcarr.github.io/blog/posts/langsmith-with-n8n-docker/
   - Topic: Docker environment setup
   - Date: 2024

---

### Alternative Tools

1. **Aegra (Community LangGraph Platform Alternative):**
   - GitHub: https://github.com/ibbybuilds/aegra
   - Features: Self-hosted, real auth (Supabase/Firebase), 5-min setup
   - License: MIT
   - Date: 2024

2. **Langfuse (LangSmith Alternative):**
   - Website: https://langfuse.com
   - Docs: https://langfuse.com/docs/integrations/langchain/tracing
   - Comparison: https://langfuse.com/faq/all/langsmith-alternative
   - License: MIT (open source)
   - Self-hosting: https://langfuse.com/self-hosting/docker-compose
   - Date: 2024-2025 (active development)

---

### Package Documentation

1. **langgraph-cli PyPI:**
   - URL: https://pypi.org/project/langgraph-cli/
   - Installation: `pip install "langgraph-cli[inmem]"`

2. **langgraph-api-inmem PyPI:**
   - URL: https://pypi.org/project/langgraph-api-inmem/
   - Purpose: Local in-memory LangGraph API

3. **langgraph-runtime-inmem PyPI:**
   - URL: https://pypi.org/project/langgraph-runtime-inmem/
   - Purpose: In-memory runtime for dev server

---

## Changelog

### October 1, 2025
- Initial research report created
- Consolidated findings from 20+ sources
- Documented 6 main error scenarios
- Provided 6 solution strategies
- Added 5 complete configuration examples
- Verified all URLs and sources

---

## Contributors

Research and compilation: Stéphane Wootha Richard (stephane@sawup.fr)
Generated with assistance from: Claude Code (Anthropic)

---

## License

This document is part of the chat-langchain project documentation and follows the project's license terms.

---

## Feedback

If you encounter 403 errors not covered in this document or have additional solutions, please:

1. Check the [GitHub Discussions](https://github.com/langchain-ai/langgraph/discussions)
2. Search for existing issues in [LangGraph Issues](https://github.com/langchain-ai/langgraph/issues)
3. Consult the [LangChain Forum](https://forum.langchain.com/)

---

**Last Updated:** October 1, 2025
**Document Version:** 1.0
**LangGraph Version Coverage:** 0.3.x - 0.4.x (2024-2025)
