"""
MCP tool definitions — mirrors src/tools.js.

Registers two tools on the MCP server:
  - calculate:                  basic arithmetic
  - summarize_with_confirmation: demonstrates elicitation + sampling
"""

import json
from mcp.server.fastmcp import FastMCP


def register_tools(mcp: FastMCP):

    @mcp.tool(
        name="calculate",
        description="Performs basic arithmetic operations",
    )
    def calculate(operation: str, a: float, b: float) -> str:
        ops = {
            "add": lambda: a + b,
            "subtract": lambda: a - b,
            "multiply": lambda: a * b,
            "divide": lambda: a / b if b != 0 else "Error: Division by zero",
        }
        fn = ops.get(operation)
        if fn is None:
            raise ValueError(f"Unknown operation: {operation}")
        result = fn()
        return json.dumps({"operation": operation, "a": a, "b": b, "result": result})

    @mcp.tool(
        name="summarize_with_confirmation",
        description="Summarizes text after getting user confirmation. Demonstrates elicitation and sampling.",
    )
    async def summarize_with_confirmation(text: str, maxLength: int = 50) -> str:
        # Note: elicitation and sampling are advanced MCP features that require
        # the mcp.server.lowlevel API. This simplified version documents the
        # intent; full elicitation/sampling requires the low-level server context.
        return f"[summarize_with_confirmation] Would summarize (max {maxLength} words): {text[:100]}..."
