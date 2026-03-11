"""
Structured output demo — mirrors 01_01_structured/app.js.

Asks the Responses API to return a strict JSON object matching a person schema
by setting text.format to a json_schema descriptor.

Usage:
    python app.py
"""

import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config_py import AI_API_KEY, EXTRA_API_HEADERS, RESPONSES_API_ENDPOINT, resolve_model_for_provider
from helpers import extract_response_text

MODEL = resolve_model_for_provider("gpt-5.4")

PERSON_SCHEMA = {
    "type": "json_schema",
    "name": "person",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "name": {
                "type": ["string", "null"],
                "description": "Full name of the person. Use null if not mentioned.",
            },
            "age": {
                "type": ["number", "null"],
                "description": "Age in years. Use null if not mentioned or unclear.",
            },
            "occupation": {
                "type": ["string", "null"],
                "description": "Job title or profession. Use null if not mentioned.",
            },
            "skills": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of skills, technologies, or competencies. Empty array if none mentioned.",
            },
        },
        "required": ["name", "age", "occupation", "skills"],
        "additionalProperties": False,
    },
}


def extract_person(text: str) -> dict:
    payload = {
        "model": MODEL,
        "input": f'Extract person information from: "{text}"',
        "text": {"format": PERSON_SCHEMA},
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

    output_text = extract_response_text(response_data)
    if not output_text:
        raise RuntimeError("Missing text output in API response")

    return json.loads(output_text)


def main():
    text = "John is 30 years old and works as a software engineer. He is skilled in JavaScript, Python, and React."
    person = extract_person(text)

    print(f"Name: {person['name'] or 'unknown'}")
    print(f"Age: {person['age'] if person['age'] is not None else 'unknown'}")
    print(f"Occupation: {person['occupation'] or 'unknown'}")
    skills = person.get("skills", [])
    print(f"Skills: {', '.join(skills) if skills else 'none'}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
