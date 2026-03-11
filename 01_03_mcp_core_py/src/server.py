#!/usr/bin/env python3
"""
MCP Server — registers tools, resources, and prompts, then listens over stdio.
Mirrors src/server.js.

Run directly:
    python src/server.py
"""

import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tools import register_tools
from src.resources import register_resources
from src.prompts import register_prompts

mcp = FastMCP("mcp-core-demo", version="1.0.0")

register_tools(mcp)
register_resources(mcp)
register_prompts(mcp)

if __name__ == "__main__":
    mcp.run(transport="stdio")
