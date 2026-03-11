"""
Helper utilities for the minimal tool-use demo — mirrors 01_02_tools/helper.js.

Provides:
 - Tool call / result extraction
 - Colored console output
 - Conversation builder
"""

import json
import os
import sys


def get_tool_calls(response: dict) -> list:
    return [item for item in response.get("output", []) if item.get("type") == "function_call"]


def get_final_text(response: dict) -> str:
    if response.get("output_text"):
        return response["output_text"]
    message = next(
        (item for item in response.get("output", []) if item.get("type") == "message"),
        None,
    )
    if message:
        content = message.get("content", [])
        if isinstance(content, list) and content:
            return content[0].get("text", "No response")
        if isinstance(content, str):
            return content
    return "No response"


# ── Color helpers ──────────────────────────────────────────────────────────────

_supports_color = sys.stdout.isatty() and not os.environ.get("NO_COLOR")

_ANSI = {
    "reset": "\x1b[0m",
    "bold": "\x1b[1m",
    "dim": "\x1b[2m",
    "blue": "\x1b[34m",
    "cyan": "\x1b[36m",
    "green": "\x1b[32m",
    "magenta": "\x1b[35m",
    "yellow": "\x1b[33m",
}


def _colorize(text: str, *styles: str) -> str:
    if not _supports_color:
        return text
    sequence = "".join(_ANSI.get(s, "") for s in styles)
    return f"{sequence}{text}{_ANSI['reset']}"


def _label(text: str, color: str) -> str:
    return _colorize(f"[{text}]", "bold", color)


def log_question(text: str):
    print(f"{_label('USER', 'blue')} {text}\n")


def log_tool_call(name: str, args: dict):
    print(f"{_label('TOOL', 'magenta')} {_colorize(name, 'bold')}")
    print(_colorize("Arguments:", "cyan"))
    print(_colorize(json.dumps(args, indent=2), "dim"))


def log_tool_result(result):
    print(_colorize("Result:", "yellow"))
    print(_colorize(json.dumps(result, indent=2), "dim"))
    print()


def log_answer(text: str):
    print(f"{_label('ASSISTANT', 'green')} {text}")


# ── Conversation helpers ───────────────────────────────────────────────────────

async def execute_tool_call(call: dict, handlers: dict) -> dict:
    import asyncio

    args = json.loads(call["arguments"])
    handler = handlers.get(call["name"])
    if not handler:
        raise ValueError(f"Unknown tool: {call['name']}")

    log_tool_call(call["name"], args)

    result = handler(args)
    if asyncio.iscoroutine(result):
        result = await result

    log_tool_result(result)

    return {
        "type": "function_call_output",
        "call_id": call["call_id"],
        "output": json.dumps(result),
    }


async def build_next_conversation(conversation: list, tool_calls: list, handlers: dict) -> list:
    import asyncio

    tool_results = await asyncio.gather(
        *(execute_tool_call(call, handlers) for call in tool_calls)
    )
    return [*conversation, *tool_calls, *tool_results]
