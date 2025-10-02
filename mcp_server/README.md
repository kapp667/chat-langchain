# LangChain Expert MCP Server

An MCP (Model Context Protocol) server that provides Claude Code with access to a sophisticated LangChain/LangGraph documentation expert powered by RAG over 15,061+ documents.

## Features

- **📚 15,061+ Indexed Documents**: Complete LangChain and LangGraph documentation
- **🤖 Multi-Agent Research**: Sophisticated query routing and research planning
- **📖 Citation-Backed Responses**: Every answer includes source references
- **💬 Session Management**: Maintain conversation context across questions
- **⚡ Multiple Models**: Choose between GPT-5 mini (fast, cost-effective), full GPT-5, GPT-4o, or Claude

## Prerequisites

1. **LangGraph Dev Server Running**:
   ```bash
   cd /Users/stephane/Documents/work/chat-langchain
   langgraph dev
   ```
   Server should be accessible at `http://localhost:2024`

2. **Python 3.10+** and **uv** (or pip) installed

3. **OpenAI API Key** configured in the main project's `.env` file

## Installation

### Step 1: Install Dependencies

Navigate to the mcp_server directory and install dependencies:
```bash
cd mcp_server
uv pip install mcp langgraph-sdk
```

This installs the required packages in the uv-managed Python environment.

### Step 2: Configure Claude Desktop

Add the MCP server to your Claude Desktop configuration:

**Location**: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add this to the `mcpServers` section:
```json
{
  "mcpServers": {
    "langchain-expert": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/stephane/Documents/work/chat-langchain/mcp_server",
        "run",
        "--no-project",
        "python",
        "langchain_expert.py"
      ],
      "env": {
        "LANGGRAPH_URL": "http://localhost:2024"
      }
    }
  }
}
```

**Important**: Replace `/Users/stephane/Documents/work/chat-langchain/mcp_server` with your actual path to the mcp_server directory.

### Step 3: Restart Claude Desktop

Close and reopen Claude Desktop to load the new MCP server.

## Usage in Claude Code

Once configured, Claude Code will have access to **4 tools**:

### 1. `ask_langchain_expert` (Primary Tool)
Ask questions about LangChain/LangGraph with configurable intelligence levels.

**Parameters:**
- `question` (required): Your question about LangChain/LangGraph
- `depth` (optional): Response depth level - **choose based on question complexity**:
  - 🏃 `"quick"` - Ultra-fast answers with GPT-4o-mini (~5-10s)
    - Best for: Simple factual questions, quick API lookups, basic concepts
  - ⚖️ `"standard"` - Balanced answers with GPT-5 mini (~10-20s) **[DEFAULT]**
    - Best for: Most questions (80% of cases), detailed explanations, troubleshooting
  - 🧠 `"deep"` - Maximum reasoning with GPT-5 full (~60-180s, max 4 minutes)
    - ⚠️ WARNING: Limited to 4 minutes by Claude Desktop timeout
    - If timeout occurs, break question into smaller parts
    - Best for: Complex architecture, multi-step reasoning, in-depth analysis
- `session_id` (optional): Session ID for conversation context

**Examples in Claude Code:**

**Simple question (quick):**
```
Use langchain_expert with depth="quick": What is LCEL?
```

**Standard detailed question (default):**
```
Use langchain_expert: How do I implement streaming in LangChain?
```

**Complex architecture (deep):**
```
Use langchain_expert with depth="deep": Design a multi-agent system with
human-in-the-loop approval and PostgreSQL checkpoints.
```

**With session for follow-ups:**
```
Ask the langchain expert about LangGraph state management (use session "arch-discussion")

[After getting response]

Ask the langchain expert how to implement that with PostgreSQL
(use the same "arch-discussion" session)
```

### 2. `clear_session` (Session Management)
Clear a conversation session to start fresh on a new topic.

**Parameters:**
- `session_id` (required): Session ID to clear

**Example:**
```
Clear the session "arch-discussion"
```

### 3. `list_sessions` [DEBUG]
View all active conversation sessions (for debugging/inspection).

**Example:**
```
List all active langchain expert sessions
```

### 4. `check_langchain_expert_status` [MONITORING]
Verify the LangChain expert system is operational and view available intelligence levels.

**Example:**
```
Check the status of the langchain expert system.
```

## Architecture

```
Claude Code
    ↓
MCP Server (langchain_expert.py)
    ↓
LangGraph SDK Client
    ↓
langgraph dev (localhost:2024)
    ↓
LangGraph Application (RAG system)
    ├── Weaviate (15,061+ docs)
    ├── PostgreSQL (checkpoints)
    └── OpenAI API (GPT models)
```

## Configuration

### Environment Variables

The MCP server uses these environment variables (optional):

- `LANGGRAPH_URL`: LangGraph server URL (default: `http://localhost:2024`)

Set in `mcp_server/.env` if needed:
```bash
LANGGRAPH_URL=http://localhost:2024
```

### Intelligence Levels (depth parameter)

The `ask_langchain_expert` tool offers 3 intelligence levels via the `depth` parameter:

| Level | Model | Response Time | Best For | Cost (approx) |
|-------|-------|---------------|----------|---------------|
| **quick** 🏃 | GPT-4o-mini | ~5-10s | Simple questions, quick lookups | ~$0.10/1M input |
| **standard** ⚖️ | GPT-5 mini | ~10-20s | Most questions (default) | ~$0.10/1M input |
| **deep** 🧠 | GPT-5 full | ~60-180s (max 4min) | Complex architecture, deep reasoning | ~$2/1M input |

**Recommendation**: Start with `standard` (default). Use `quick` for simple lookups, `deep` only for truly complex architectural questions.

## Troubleshooting

### "Connection error: Cannot reach LangGraph server"

**Solution**: Ensure `langgraph dev` is running:
```bash
cd /Users/stephane/Documents/work/chat-langchain
langgraph dev
```

Check it's accessible:
```bash
curl http://localhost:2024/health
```

### "Request timed out"

**Causes**:
- Question too complex
- Server overloaded
- Model processing slowly

**Solutions**:
1. Break question into simpler parts
2. Increase timeout parameter
3. Check server logs: `tail -50 /tmp/langgraph_dev.log`

### "No response received"

**Solution**: Check LangGraph dev logs for errors:
```bash
tail -100 /tmp/langgraph_dev.log | grep -E "(error|ERROR|exception)"
```

### MCP Server Not Appearing in Claude Desktop

**Solutions**:
1. Verify configuration file location and JSON syntax
2. Restart Claude Desktop completely (Cmd+Q, then reopen)
3. Check Claude Desktop logs: `~/Library/Logs/Claude/`

## Development

### Running Tests

```bash
cd mcp_server
uv run pytest
```

### Code Quality

```bash
# Lint
uv run ruff check .

# Format
uv run ruff format .
```

### Debugging

Enable verbose logging by running the server directly:
```bash
cd mcp_server
uv run python langchain_expert.py
```

## Performance

**Typical response times**:
- Simple questions (GPT-5 mini): 3-8 seconds
- Complex questions (GPT-5 full): 8-20 seconds
- Alternative models (GPT-4o, Claude): 5-15 seconds

**Factors affecting speed**:
- Model selected (mini < full GPT-5)
- Question complexity (routing + research steps)
- Number of documents retrieved (typically 10-30)
- Network latency to OpenAI API

## Limitations

1. **Requires langgraph dev running**: Server must be accessible on localhost:2024
2. **OpenAI API costs**: Using GPT models incurs API costs (GPT-5 mini is cost-effective default)
3. **Rate limits**: Subject to OpenAI API rate limits
4. **Memory**: Sessions stored in-memory only (cleared on server restart)

## Future Enhancements

Potential improvements (not currently implemented):

- [ ] Persistent session storage (Redis/file-based)
- [ ] Response caching for identical questions
- [ ] Streaming responses in Claude Code interface
- [ ] Usage metrics and cost tracking
- [ ] Support for local models (Ollama)
- [ ] Multi-language documentation support

## License

Same as parent project (chat-langchain).

## Support

For issues or questions:
1. Check logs: `/tmp/langgraph_dev.log`
2. Verify langgraph dev status: `curl http://localhost:2024/health`
3. Review CLAUDE.md in parent directory for system context

## Related Documentation

- **Main Project**: `/Users/stephane/Documents/work/chat-langchain/`
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **MCP Specification**: https://modelcontextprotocol.io/
- **LangGraph SDK**: https://github.com/langchain-ai/langgraph/tree/main/libs/sdk-py
