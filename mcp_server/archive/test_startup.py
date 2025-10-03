#!/usr/bin/env python3
"""Quick test to verify MCP server can start without errors."""

import sys
import os

# Set environment variable
os.environ["LANGGRAPH_URL"] = "http://localhost:2024"

try:
    print("Testing MCP server startup...")
    print(f"LANGGRAPH_URL: {os.environ.get('LANGGRAPH_URL')}")

    # Import dependencies
    import mcp
    from mcp.server.fastmcp import FastMCP
    from langgraph_sdk import get_client

    print("✅ Imports successful")

    # Test LangGraph connection (synchronous check)
    import urllib.request
    import json

    url = f"{os.environ['LANGGRAPH_URL']}/info"
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read())
        print(f"✅ LangGraph connection OK - Version: {data.get('version')}")

    # Create MCP server instance
    mcp_server = FastMCP("LangChain Expert")
    print("✅ MCP server instance created")

    print("\n✅ All startup checks passed!")
    print("The MCP server should work correctly in Claude Desktop.")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
