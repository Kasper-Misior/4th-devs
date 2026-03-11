"""Sandbox path utilities — mirrors src/utils/sandbox.js."""

import shutil
from pathlib import Path
from src.config import SANDBOX_ROOT


def initialize_sandbox():
    """Wipe and recreate the sandbox directory."""
    if SANDBOX_ROOT.exists():
        shutil.rmtree(SANDBOX_ROOT)
    SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)


def resolve_sandbox_path(relative_path: str) -> Path:
    """Resolve a relative path inside the sandbox, raising on traversal attempts."""
    resolved = (SANDBOX_ROOT / relative_path).resolve()
    try:
        resolved.relative_to(SANDBOX_ROOT.resolve())
    except ValueError:
        raise PermissionError(f'Access denied: path "{relative_path}" is outside sandbox')
    return resolved
