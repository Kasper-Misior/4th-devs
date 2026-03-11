"""
MCP prompt definitions — mirrors src/prompts.js.

Prompts are reusable message templates with parameters.
"""

from mcp.server.fastmcp import FastMCP
from mcp.types import GetPromptResult, PromptMessage, TextContent


def register_prompts(mcp: FastMCP):

    @mcp.prompt(name="code-review", description="Template for code review requests")
    def code_review(code: str, language: str = "unknown", focus: str = "all") -> GetPromptResult:
        focus_map = {
            "security": "Focus on security vulnerabilities and input validation.",
            "performance": "Focus on performance and optimization.",
            "readability": "Focus on code clarity and maintainability.",
            "all": "Review for security, performance, and readability.",
        }
        focus_text = focus_map.get(focus, focus_map["all"])
        content = f"Review this {language} code.\n\n{focus_text}\n\n```{language}\n{code}\n```"
        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=content),
                )
            ]
        )
