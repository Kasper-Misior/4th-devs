"""AI provider client — mirrors src/ai.js."""

import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config_py import AI_API_KEY, EXTRA_API_HEADERS, RESPONSES_API_ENDPOINT


def _extract_text(data: dict) -> str:
    output_text = data.get("output_text")
    if isinstance(output_text, str):
        return output_text.strip()

    output = data.get("output", [])
    message = next((o for o in output if isinstance(o, dict) and o.get("type") == "message"), None)
    if message:
        content = message.get("content", [])
        part = next((c for c in content if isinstance(c, dict) and c.get("type") == "output_text"), None)
        if part:
            return (part.get("text") or "").strip()
    return ""


def completion(*, model: str, input_messages, max_output_tokens: int = 500) -> str:
    """Call the Responses API and return the text output."""
    payload = {"model": model, "input": input_messages, "max_output_tokens": max_output_tokens}
    data = json.dumps(payload).encode()
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
        body = json.loads(e.read())
        msg = body.get("error", {}).get("message") or f"API request failed ({e.code})"
        raise RuntimeError(msg)

    if response_data.get("error"):
        raise RuntimeError(response_data["error"].get("message", "Unknown API error"))

    text = _extract_text(response_data)
    if not text:
        raise RuntimeError("Empty response")
    return text
