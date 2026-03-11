"""Filesystem tool handlers — mirrors src/tools/handlers.js."""

import os
from datetime import datetime, timezone
from pathlib import Path
from src.utils.sandbox import resolve_sandbox_path


def list_files(args: dict) -> list:
    full_path = resolve_sandbox_path(args["path"])
    entries = []
    for entry in sorted(full_path.iterdir()):
        entries.append({
            "name": entry.name,
            "type": "directory" if entry.is_dir() else "file",
        })
    return entries


def read_file(args: dict) -> dict:
    full_path = resolve_sandbox_path(args["path"])
    content = full_path.read_text(encoding="utf-8")
    return {"content": content}


def write_file(args: dict) -> dict:
    full_path = resolve_sandbox_path(args["path"])
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(args["content"], encoding="utf-8")
    return {"success": True, "message": f"File written: {args['path']}"}


def delete_file(args: dict) -> dict:
    full_path = resolve_sandbox_path(args["path"])
    full_path.unlink()
    return {"success": True, "message": f"File deleted: {args['path']}"}


def create_directory(args: dict) -> dict:
    full_path = resolve_sandbox_path(args["path"])
    full_path.mkdir(parents=True, exist_ok=True)
    return {"success": True, "message": f"Directory created: {args['path']}"}


def file_info(args: dict) -> dict:
    full_path = resolve_sandbox_path(args["path"])
    stat = full_path.stat()
    return {
        "size": stat.st_size,
        "isDirectory": full_path.is_dir(),
        "created": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
    }


HANDLERS = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "delete_file": delete_file,
    "create_directory": create_directory,
    "file_info": file_info,
}
