"""Tool-calling execution loop — mirrors src/executor.js."""

import json
from src.api import chat, extract_tool_calls, extract_text

MAX_TOOL_ROUNDS = 10


def _log_query(query: str):
    print(f"\n{'=' * 60}")
    print(f"Query: {query}")
    print("=" * 60)


def _log_result(text: str):
    print(f"\nA: {text}")


def _execute_tool_calls(tool_calls: list, handlers: dict) -> list:
    print(f"\nTool calls: {len(tool_calls)}")
    results = []
    for call in tool_calls:
        args = json.loads(call["arguments"])
        print(f"  → {call['name']}({json.dumps(args)})")
        try:
            handler = handlers.get(call["name"])
            if not handler:
                raise ValueError(f"Unknown tool: {call['name']}")
            result = handler(args)
            print("    ✓ Success")
        except Exception as e:
            print(f"    ✗ Error: {e}")
            result = {"error": str(e)}

        results.append({
            "type": "function_call_output",
            "call_id": call["call_id"],
            "output": json.dumps(result),
        })
    return results


def process_query(query: str, *, model: str, tools: list, handlers: dict, instructions: str = None) -> str:
    _log_query(query)
    conversation = [{"role": "user", "content": query}]

    for _ in range(MAX_TOOL_ROUNDS):
        response = chat(
            model=model,
            input_messages=conversation,
            tools=tools,
            instructions=instructions,
        )
        tool_calls = extract_tool_calls(response)

        if not tool_calls:
            text = extract_text(response) or "No response"
            _log_result(text)
            return text

        tool_results = _execute_tool_calls(tool_calls, handlers)
        conversation = [*conversation, *tool_calls, *tool_results]

    _log_result("Max tool rounds reached")
    return "Max tool rounds reached"
