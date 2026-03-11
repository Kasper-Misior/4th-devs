"""Responses API client for tool-use — mirrors src/api.js."""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config_py import AI_API_KEY, EXTRA_API_HEADERS, RESPONSES_API_ENDPOINT


def chat(*, model: str, input_messages: list, tools=None, tool_choice="auto", instructions=None) -> dict:
    body = {"model": model, "input": input_messages}
    if tools:
        body["tools"] = tools
        body["tool_choice"] = tool_choice
    if instructions:
        body["instructions"] = instructions

    data = json.dumps(body).encode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AI_API_KEY}",
        **EXTRA_API_HEADERS,
    }

    req = urllib.request.Request(RESPONSES_API_ENDPOINT, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            response_data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_err = json.loads(e.read())
        msg = body_err.get("error", {}).get("message") or f"Request failed with status {e.code}"
        raise RuntimeError(msg)

    if response_data.get("error"):
        raise RuntimeError(response_data["error"].get("message", "Unknown API error"))

    return response_data


def extract_tool_calls(response: dict) -> list:
    return [item for item in response.get("output", []) if item.get("type") == "function_call"]


def extract_text(response: dict):
    output_text = response.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text
    message = next((item for item in response.get("output", []) if item.get("type") == "message"), None)
    if message:
        content = message.get("content", [])
        if isinstance(content, list) and content:
            return content[0].get("text")
    return None
