"""
MCP Core Demo — exercises all MCP capabilities via stdio transport.
Mirrors 01_03_mcp_core/app.js.

The client spawns the server as a subprocess and communicates via stdin/stdout.
This is how real MCP integrations work (e.g. Claude Desktop, Cursor).

Usage:
    python app.py

Requires:
    pip install mcp python-dotenv
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from config_py import resolve_model_for_provider
from src.log import heading, log, parse_tool_result, client_log

MODEL = resolve_model_for_provider("gpt-5.1")
SERVER_PATH = Path(__file__).parent / "src" / "server.py"


async def main():
    client_log.spawning_server(str(SERVER_PATH))

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as client:
            await client.initialize()
            client_log.connected()

            # ── TOOLS ──────────────────────────────────────────────────────────
            heading("TOOLS", "Actions the server exposes for the LLM to invoke")

            tools_result = await client.list_tools()
            log("listTools", [f"{t.name} — {t.description}" for t in tools_result.tools])

            calc_result = await client.call_tool("calculate", {"operation": "multiply", "a": 42, "b": 17})
            log("callTool(calculate)", parse_tool_result(calc_result.model_dump()))

            summary_result = await client.call_tool(
                "summarize_with_confirmation",
                {
                    "text": (
                        "The Model Context Protocol (MCP) is a standardized protocol that allows "
                        "applications to provide context for LLMs. It separates the concerns of "
                        "providing context from the actual LLM interaction. MCP servers expose "
                        "tools, resources, and prompts that clients can discover and use."
                    ),
                    "maxLength": 30,
                },
            )
            log("callTool(summarize_with_confirmation)", parse_tool_result(summary_result.model_dump()))

            # ── RESOURCES ──────────────────────────────────────────────────────
            heading("RESOURCES", "Read-only data the server makes available to clients")

            resources_result = await client.list_resources()
            log(
                "listResources",
                [f"{r.uri} — {r.name or r.description}" for r in resources_result.resources],
            )

            config_resource = await client.read_resource("config://project")
            import json
            log("readResource(config://project)", json.loads(config_resource.contents[0].text))

            stats_resource = await client.read_resource("data://stats")
            log("readResource(data://stats)", json.loads(stats_resource.contents[0].text))

            # ── PROMPTS ────────────────────────────────────────────────────────
            heading("PROMPTS", "Reusable message templates with parameters")

            prompts_result = await client.list_prompts()
            log("listPrompts", [f"{p.name} — {p.description}" for p in prompts_result.prompts])

            prompt_result = await client.get_prompt(
                "code-review",
                {
                    "code": "function add(a, b) { return a + b; }",
                    "language": "javascript",
                    "focus": "readability",
                },
            )
            log(
                "getPrompt(code-review)",
                [
                    f"[{m.role}] {m.content.text if hasattr(m.content, 'text') else str(m.content)}"
                    for m in prompt_result.messages
                ],
            )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
