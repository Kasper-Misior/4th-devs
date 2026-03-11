"""Logging helpers for the MCP core demo — mirrors src/log.js."""

import json

_C = {
    "reset": "\x1b[0m",
    "bold": "\x1b[1m",
    "dim": "\x1b[2m",
    "red": "\x1b[31m",
    "green": "\x1b[32m",
    "yellow": "\x1b[33m",
    "cyan": "\x1b[36m",
    "magenta": "\x1b[35m",
}


def _c(key: str) -> str:
    return _C.get(key, "")


def _truncate(value, max_length: int = 50) -> str:
    text = str(value)
    return text[:max_length] + "..." if len(text) > max_length else text


def heading(title: str, description: str = ""):
    print(f"\n{_c('bold')}═══ {title} ═══{_c('reset')}")
    if description:
        print(f"{_c('dim')}{description}{_c('reset')}")


def log(label: str, data=None):
    print(f"\n{_c('bold')}{_c('cyan')}▶ {label}{_c('reset')}")
    if data is None:
        return
    if isinstance(data, list):
        lines = [str(item) for item in data]
    elif isinstance(data, str):
        lines = [data]
    else:
        lines = json.dumps(data, indent=2).splitlines()
    for line in lines:
        print(f"{_c('dim')}  {line}{_c('reset')}")


def parse_tool_result(result: dict):
    content = result.get("content", [])
    text = next((c["text"] for c in content if c.get("type") == "text"), "")
    if result.get("isError"):
        raise RuntimeError(text or "Tool call failed")
    try:
        return json.loads(text)
    except Exception:
        return text


class _ClientLog:
    def spawning_server(self, server_path: str):
        print(f"\n{_c('green')}🚀 Spawning MCP server: {server_path}{_c('reset')}")

    def connected(self):
        print(f"{_c('green')}✓ Connected to MCP server via stdio{_c('reset')}")

    def sampling_request(self, params: dict):
        messages = params.get("messages", [])
        max_tokens = params.get("maxTokens", "default")
        print(f"\n{_c('magenta')}  📡 Sampling — server asked the client to call an LLM{_c('reset')}")
        print(f"{_c('dim')}     Messages: {len(messages)}, max tokens: {max_tokens}{_c('reset')}")

    def sampling_response(self, text: str):
        print(f"{_c('dim')}     LLM responded: \"{_truncate(text)}\"{_c('reset')}")

    def sampling_error(self, cause):
        msg = str(cause)
        print(f"{_c('red')}     Sampling error: {msg}{_c('reset')}")

    def elicitation_request(self, params: dict):
        mode = params.get("mode", "unknown")
        print(f"\n{_c('yellow')}  🔔 Elicitation — server asked the client for user confirmation{_c('reset')}")
        print(f"{_c('dim')}     Mode: {mode}{_c('reset')}")

    def auto_accepted_elicitation(self, content: dict):
        import json
        print(f"{_c('dim')}     Auto-accepted with: {json.dumps(content)}{_c('reset')}")


client_log = _ClientLog()
