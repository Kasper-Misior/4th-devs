"""
Multi-turn chat demo — mirrors 01_01_interaction/app.js.

Demonstrates passing conversation history to the Responses API so the model
can answer follow-up questions that refer to earlier responses.

Usage:
    python app.py
"""

import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

# Allow imports from the repo root (config_py.py lives there)
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_py import AI_API_KEY, EXTRA_API_HEADERS, RESPONSES_API_ENDPOINT, resolve_model_for_provider
from helpers import extract_response_text, to_message

MODEL = resolve_model_for_provider("gpt-5.2")


def chat(input_text: str, history: list = None) -> dict:
    """Send a message (with optional history) and return {text, reasoning_tokens}."""
    if history is None:
        history = []

    payload = {
        "model": MODEL,
        "input": [*history, to_message("user", input_text)],
        "reasoning": {"effort": "medium"},
    }

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
        message = body.get("error", {}).get("message") or f"Request failed with status {e.code}"
        raise RuntimeError(message)

    if response_data.get("error"):
        raise RuntimeError(response_data["error"].get("message", "Unknown API error"))

    text = extract_response_text(response_data)
    if not text:
        raise RuntimeError("Missing text output in API response")

    reasoning_tokens = (
        response_data.get("usage", {})
        .get("output_tokens_details", {})
        .get("reasoning_tokens", 0)
    )

    return {"text": text, "reasoning_tokens": reasoning_tokens}


def main():
    first_question = "What is 25 * 48?"
    first_answer = chat(first_question)

    second_question = "Divide that by 4."
    second_question_context = [
        {"type": "message", "role": "user", "content": first_question},
        {"type": "message", "role": "assistant", "content": first_answer["text"]},
    ]
    second_answer = chat(second_question, second_question_context)

    print(f"Q: {first_question}")
    print(f"A: {first_answer['text']} ({first_answer['reasoning_tokens']} reasoning tokens)")
    print(f"Q: {second_question}")
    print(f"A: {second_answer['text']} ({second_answer['reasoning_tokens']} reasoning tokens)")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
