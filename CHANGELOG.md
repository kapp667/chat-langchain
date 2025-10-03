# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed - 2025-10-02 (Evening)

- **MCP Server Refactored with Intelligence Levels**: Simplified from 5 to 4 tools with configurable depth
  - **Removed** `ask_langchain_expert_advanced` (redundant wrapper)
  - **Added** `depth` parameter to `ask_langchain_expert` with 3 intelligence levels:
    - `"quick"`: GPT-4o-mini (~5-10s) for simple questions
    - `"standard"`: GPT-5 mini (~10-20s) for most questions [DEFAULT]
    - `"deep"`: GPT-5 full (~60-180s, max 4min) for complex architecture analysis
  - **Refactored** internal implementation with DRY principle (function `_ask_expert_internal`)
  - Timeout adapted per level: 60s (quick), 120s (standard), 240s (deep)
  - **Note**: Deep mode limited to 4 minutes by Claude Desktop client timeout (discovered during testing)
  - Files: `mcp_server/langchain_expert.py` (341 lines, from 309)

- **Documentation Updated** for 4-tool architecture:
  - `mcp_server/README.md`: Intelligence levels table, updated tool descriptions
  - `mcp_server/STATUS.md`: 4 tools with depth configuration
  - Tagged tools: [PRIMARY], [DEBUG], [MONITORING] for clarity

### Added - 2025-10-02 (Afternoon)

- **MCP Server Implementation**: Complete Model Context Protocol server for Claude Desktop integration
  - 4 tools exposed: `ask_langchain_expert` (with depth), `check_langchain_expert_status`, `list_sessions`, `clear_session`
  - Thread management with session caching for multi-turn conversations
  - Streaming support via LangGraph SDK
  - Configurable intelligence levels optimized for speed vs depth
  - Files: `mcp_server/langchain_expert.py` (341 lines)

- **MCP Documentation Suite**: Comprehensive documentation for MCP server (1,498 total lines)
  - `mcp_server/README.md` (302 lines): Technical documentation
  - `mcp_server/MANUAL_START.md` (252 lines): Daily operations guide
  - `mcp_server/STATUS.md` (220 lines): Project status snapshot
  - `mcp_server/QUICK_START.md` (92 lines): Quick start testing guide
  - `mcp_server/VERIFICATION_COMPLETE.md`: System verification summary

- **Claude Desktop Integration**: MCP server configuration
  - Config file: `~/Library/Application Support/Claude/claude_desktop_config.json`
  - Coexists with existing `youtube` MCP server
  - Environment variable: `LANGGRAPH_URL=http://localhost:2024`

### Changed - 2025-10-02

- **CLAUDE.md Restructure**: Condensed from investigation history to operational guide (632 lines)
  - Removed verbose investigation logs from September 30, 2025
  - Preserved critical technical decisions and architecture documentation
  - Added MCP server section with complete integration details
  - Updated "Current Project State" to reflect MCP operational status
  - Moved detailed migration analysis to separate docs (ANALYSE_LANGSERVE_VS_MASTER.md, MASTER_SELF_HOSTING_ANALYSIS.md)

- **Backend Model Configuration**: Updated to GPT-5 mini for cost-effectiveness
  - File: `backend/retrieval_graph/configuration.py`
  - `query_model`: Changed from `openai/gpt-5` to `openai/gpt-5-mini-2025-08-07`
  - `response_model`: Changed from `openai/gpt-5` to `openai/gpt-5-mini-2025-08-07`
  - Cost reduction: ~95% cheaper than GPT-5 while maintaining quality

### Fixed - 2025-10-02

- **MCP Thread Creation Bug**: Fixed thread ID generation
  - Changed from local UUID generation to LangGraph API thread creation
  - Prevents HTTP 404 errors during streaming
  - Files: `mcp_server/langchain_expert.py`

- **MCP Streaming API Signature**: Corrected parameter ordering
  - Changed `thread_id` and `assistant_id` from named to positional parameters
  - Based on analysis of frontend code (`frontend/app/contexts/GraphContext.tsx:105`)
  - Ensures proper streaming functionality

- **MCP Timeout Configuration**: Increased default timeout
  - Changed from 60s to 180s to accommodate GPT-5 mini initialization
  - First query: ~180s, subsequent queries: 8-20s

### Documentation - 2025-10-02

- **Investigation Archive**: Detailed analysis documents preserved separately
  - `ANALYSE_LANGSERVE_VS_MASTER.md`: Branch comparison and migration strategy
  - `MASTER_SELF_HOSTING_ANALYSIS.md`: Self-hosting feasibility deep dive
  - `PLAN_DE_MIGRATION.md`: LangChain 0.3 + Weaviate v4 migration plan

- **Setup Guides**: Comprehensive local deployment documentation
  - `STACK_LOCAL_EXPLAINED.md`: Complete architecture guide (479 lines)
  - `LANGGRAPH_DEV_VS_CLOUD.md`: Operational comparison (983 lines)
  - `SETUP_SELF_HOSTED.md`: Self-hosting setup instructions

## [Previous Work] - 2025-09-30 to 2025-10-01

### Added

- **100% Self-Hosted Deployment**: Master branch running locally without LangGraph Cloud
  - Docker stack: PostgreSQL 16 + Weaviate 1.32 + Redis 7
  - 15,061 documents successfully indexed (LangChain + LangGraph)
  - Full feature parity with cloud deployment (all intelligence intact)
  - Cost: $20-50/month (OpenAI only) vs $285-385/month (full cloud)

- **GPT-5 Integration**: OpenAI GPT-5 model support
  - Model: `openai/gpt-5-2024-08-07`
  - Temperature requirement: 1.0 (API constraint)
  - Integration tested and validated with production prompts

### Changed

- **Production Prompts**: Extracted from LangChain git history (commit c0de6a3^, Oct 2024)
  - File: `backend/prompts.py`
  - Replaced private LangSmith Hub references (langchain-ai/* prompts are 403 Forbidden)
  - Battle-tested prompts from chat.langchain.com production

- **Weaviate Configuration**: Auto-detection for local/cloud deployment
  - File: `backend/ingest.py`
  - Detects localhost in WEAVIATE_URL
  - Switches between `connect_to_local()` and `connect_to_weaviate_cloud()`
  - Zero code duplication, portable configuration

### Documentation

- Branch strategy analysis and migration feasibility studies
- Complete self-hosting architecture documentation
- LangSmith 403 error troubleshooting guide

---

## Format Notes

- **feat**: New features
- **fix**: Bug fixes
- **docs**: Documentation changes
- **chore**: Maintenance tasks
- **refactor**: Code refactoring

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Stéphane Wootha Richard <stephane@sawup.fr>
