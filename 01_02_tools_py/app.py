"""
Minimal tool-use demo — mirrors 01_02_tools/app.js.

Defines two tools (get_weather, send_email), runs a tool-calling loop with
web search enabled, and prints the final answer.

Usage:
    python app.py
"""

import sys
import json
import asyncio
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config_py import (
    AI_API_KEY,
    EXTRA_API_HEADERS,
    RESPONSES_API_ENDPOINT,
    build_responses_request,
    resolve_model_for_provider,
)
from helper import (
    get_tool_calls,
    get_final_text,
    log_question,
    log_answer,
    build_next_conversation,
)

MODEL = resolve_model_for_provider("gpt-4.1-mini")
WEB_SEARCH = True

# ── Tool definitions ────────────────────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "name": "get_weather",
        "description": "Get current weather for a given location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
            },
            "required": ["location"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "send_email",
        "description": "Send a short email message to a recipient",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Plain-text email body"},
            },
            "required": ["to", "subject", "body"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]

# ── Tool handlers ───────────────────────────────────────────────────────────────

def _require_text(value, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'"{field_name}" must be a non-empty string.')
    return value.strip()


WEATHER_DATA = {
    "Kraków": {"temp": -2, "conditions": "snow"},
    "London": {"temp": 8, "conditions": "rain"},
    "Tokyo": {"temp": 15, "conditions": "cloudy"},
}


def get_weather(args: dict) -> dict:
    city = _require_text(args.get("location", ""), "location")
    return WEATHER_DATA.get(city, {"temp": None, "conditions": "unknown"})


def send_email(args: dict) -> dict:
    recipient = _require_text(args.get("to", ""), "to")
    subject = _require_text(args.get("subject", ""), "subject")
    body = _require_text(args.get("body", ""), "body")
    return {"success": True, "status": "sent", "to": recipient, "subject": subject, "body": body}


HANDLERS = {
    "get_weather": get_weather,
    "send_email": send_email,
}

# ── API call ────────────────────────────────────────────────────────────────────

def request_response(input_messages: list) -> dict:
    body = build_responses_request(
        model=MODEL,
        input=input_messages,
        tools=TOOLS,
        web_search=WEB_SEARCH,
    )
    data = json.dumps(body).encode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AI_API_KEY}",
        **EXTRA_API_HEADERS,
    }
    req = urllib.request.Request(RESPONSES_API_ENDPOINT, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_err = json.loads(e.read())
        msg = body_err.get("error", {}).get("message") or f"Request failed ({e.code})"
        raise RuntimeError(msg)


MAX_TOOL_STEPS = 5


async def chat(conversation: list) -> str:
    current = conversation
    for _ in range(MAX_TOOL_STEPS):
        response = request_response(current)
        tool_calls = get_tool_calls(response)

        if not tool_calls:
            return get_final_text(response)

        current = await build_next_conversation(current, tool_calls, HANDLERS)

    raise RuntimeError(f"Tool calling did not finish within {MAX_TOOL_STEPS} steps.")


async def main():
    query = "Use web search to check the current weather in Kraków. Then send a short email with the answer to student@example.com."
    log_question(query)
    answer = await chat([{"role": "user", "content": query}])
    log_answer(answer)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
