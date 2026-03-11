"""
MCP Client — connects to a server over stdio, exercises capabilities.
Mirrors src/client.js.

Spawns server.py as a subprocess and communicates via stdin/stdout.
"""

import sys
import asyncio
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.log import client_log

_SERVER_PATH = Path(__file__).parent / "server.py"


async def create_mcp_client(*, model: str, server_path: Path = None):
    """
    Spawn the MCP server and return a connected ClientSession.

    Returns an async context manager — use `async with create_mcp_client(...) as client`.
    """
    resolved_path = server_path or _SERVER_PATH
    client_log.spawning_server(str(resolved_path))

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(resolved_path)],
    )
    return stdio_client(server_params)
