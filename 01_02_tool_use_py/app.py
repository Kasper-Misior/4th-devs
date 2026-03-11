"""
Sandboxed filesystem tool demo — mirrors 01_02_tool_use/app.js.

Runs a set of predefined queries against a sandboxed filesystem using
tool-calling. Each query is isolated (fresh conversation state).

Usage:
    python app.py
"""

import sys
from pathlib import Path

# Allow root-level config_py.py to be found
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from src.config import API
from src.executor import process_query
from src.tools import TOOLS, HANDLERS
from src.utils.sandbox import initialize_sandbox

QUERIES = [
    "What files are in the sandbox?",
    "Create a file called hello.txt with content: 'Hello, World!'",
    "Read the hello.txt file",
    "Get info about hello.txt",
    "Create a directory called 'docs'",
    "Create a file docs/readme.txt with content: 'Documentation folder'",
    "List files in the docs directory",
    "Delete the hello.txt file",
    "Try to read ../config.py",  # Security test — path traversal blocked
]


def main():
    initialize_sandbox()
    print("Sandbox prepared: empty state\n")

    for query in QUERIES:
        process_query(
            query,
            model=API["model"],
            tools=TOOLS,
            handlers=HANDLERS,
            instructions=API["instructions"],
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
