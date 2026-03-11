"""Helpers for parsing Responses API output — mirrors helpers.js."""


def extract_response_text(data: dict) -> str:
    """Return the text output from a Responses API response dict."""
    output_text = data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    output = data.get("output", [])
    messages = [item for item in output if isinstance(item, dict) and item.get("type") == "message"]

    for message in messages:
        content = message.get("content", [])
        if not isinstance(content, list):
            continue
        for part in content:
            if isinstance(part, dict) and part.get("type") == "output_text" and isinstance(part.get("text"), str):
                return part["text"]

    return ""


def to_message(role: str, content: str) -> dict:
    return {"type": "message", "role": role, "content": content}
