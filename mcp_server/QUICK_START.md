# Quick Start - Test MCP Server Now

## ✅ Phase 1.1 - Configuration (DONE)

The MCP server has been added to Claude Desktop configuration at:
`~/Library/Application Support/Claude/claude_desktop_config.json`

Configuration includes:
- **youtube** server (already configured)
- **langchain-expert** server (newly added)

## 📋 Phase 1.2 - Restart Claude Desktop

**IMPORTANT**: You must restart Claude Desktop to load the new MCP server.

### Steps:
1. **Quit Claude Desktop completely**: Press `Cmd+Q` (not just close the window)
2. **Reopen Claude Desktop** from Applications or Spotlight

### Verification:
Claude Desktop will attempt to connect to the MCP server on startup. Check the MCP icon/status in the interface.

## 🧪 Phase 1.3 - Test the MCP Server

### Prerequisites Check:
Ensure `langgraph dev` is running:
```bash
curl http://localhost:2024/health 2>/dev/null || echo "Server may not be ready yet"
ps aux | grep "langgraph dev" | grep -v grep
```

### Test Commands in Claude Code:

1. **List available tools:**
   ```
   Quels outils MCP sont disponibles maintenant ?
   ```

2. **Test simple question:**
   ```
   Utilise l'outil langchain_expert pour expliquer ce qu'est LangChain en quelques lignes.
   ```

3. **Test complex question:**
   ```
   Utilise langchain_expert pour m'expliquer comment fonctionnent les checkpoints LangGraph avec PostgreSQL.
   ```

4. **Check system status:**
   ```
   Utilise check_langchain_expert_status pour vérifier que le système est opérationnel.
   ```

### Expected Results:

✅ **5 tools should be available:**
- `ask_langchain_expert` - Main query tool (uses GPT-5 mini)
- `ask_langchain_expert_advanced` - Complex queries (uses full GPT-5)
- `check_langchain_expert_status` - System health check
- `list_sessions` - View active conversation sessions
- `clear_session` - Clear a session

✅ **Response should include:**
- Detailed answer from LangGraph backend
- Citations with numbered references [1], [2], etc.
- Links to documentation sources
- Structured, expert-level content

### Troubleshooting:

**MCP server not appearing:**
- Verify config file syntax: `cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python3 -m json.tool`
- Check Claude Desktop logs: `~/Library/Logs/Claude/`
- Ensure complete restart (Cmd+Q, not just window close)

**Connection errors:**
- Verify langgraph dev is running: `curl http://localhost:2024/health`
- Check logs: `tail -50 /tmp/langgraph_dev.log`
- Restart langgraph dev if needed

**Timeout errors:**
- First query may take 180s (model initialization)
- Subsequent queries: 8-20 seconds
- Check `timeout` parameter if needed

---

## 🚀 Next: Phase 2 - Automatic Startup

Once Phase 1 testing is successful, proceed to Phase 2 for automatic startup on boot.

See `AUTOSTART_GUIDE.md` (will be created in Phase 2.4)
