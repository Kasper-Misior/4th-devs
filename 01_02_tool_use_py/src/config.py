"""Configuration for the sandboxed filesystem tool demo — mirrors src/config.js."""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config_py import resolve_model_for_provider

SANDBOX_ROOT = Path(__file__).parent.parent / "sandbox"
SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)

API = {
    "model": resolve_model_for_provider("gpt-4.1"),
    "instructions": (
        "You are a helpful assistant with access to a sandboxed filesystem.\n"
        "You can list, read, write, and delete files within the sandbox.\n"
        "Always use the available tools to interact with files.\n"
        "Be concise in your responses."
    ),
}
