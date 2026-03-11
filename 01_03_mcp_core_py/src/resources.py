"""
MCP resource definitions — mirrors src/resources.js.

Resources are read-only data the server exposes:
  - config://project  — static project metadata
  - data://stats      — dynamic runtime statistics
"""

import json
import time
from mcp.server.fastmcp import FastMCP

_START_TIME = time.time()
_request_count = 0


def register_resources(mcp: FastMCP):

    @mcp.resource("config://project")
    def project_config() -> str:
        return json.dumps({
            "name": "mcp-core-demo",
            "version": "1.0.0",
            "features": ["tools", "resources", "prompts", "elicitation", "sampling"],
        }, indent=2)

    @mcp.resource("data://stats")
    def runtime_stats() -> str:
        global _request_count
        _request_count += 1
        return json.dumps({
            "uptime_seconds": int(time.time() - _START_TIME),
            "request_count": _request_count,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }, indent=2)
