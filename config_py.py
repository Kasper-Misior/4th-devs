"""
Root configuration module — mirrors config.js.

Loads .env, validates API keys, resolves provider, and builds request helpers.
Requires Python 3.8+ and the `python-dotenv` package (pip install python-dotenv).
"""

import os
import sys
from pathlib import Path

MIN_PYTHON_VERSION = (3, 8)

ROOT_DIR = Path(__file__).parent
ROOT_ENV_FILE = ROOT_DIR / ".env"

RESPONSES_ENDPOINTS = {
    "openai": "https://api.openai.com/v1/responses",
    "openrouter": "https://openrouter.ai/api/v1/responses",
}

OPENROUTER_ONLINE_SUFFIX = ":online"
VALID_OPENAI_SEARCH_CONTEXT_SIZES = {"low", "medium", "high"}
VALID_OPENROUTER_WEB_ENGINES = {"native", "exa"}
VALID_PROVIDERS = {"openai", "openrouter"}

# Check Python version
if sys.version_info < MIN_PYTHON_VERSION:
    print(f"\033[31mError: Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+ is required\033[0m", file=sys.stderr)
    print(f"       Current version: {sys.version}", file=sys.stderr)
    sys.exit(1)

# Load .env file if it exists
if ROOT_ENV_FILE.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT_ENV_FILE)
    except ImportError:
        # Fallback: parse .env manually if dotenv not installed
        with open(ROOT_ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())
    except Exception as e:
        print(f"\033[31mError: Failed to load .env file\033[0m", file=sys.stderr)
        print(f"       File: {ROOT_ENV_FILE}", file=sys.stderr)
        print(f"       Reason: {e}", file=sys.stderr)
        sys.exit(1)

OPENAI_API_KEY = (os.environ.get("OPENAI_API_KEY") or "").strip()
OPENROUTER_API_KEY = (os.environ.get("OPENROUTER_API_KEY") or "").strip()
_requested_provider = (os.environ.get("AI_PROVIDER") or "").strip().lower()

_has_openai_key = bool(OPENAI_API_KEY)
_has_openrouter_key = bool(OPENROUTER_API_KEY)

if not _has_openai_key and not _has_openrouter_key:
    print("\033[31mError: API key is not set\033[0m", file=sys.stderr)
    print(f"       Create: {ROOT_ENV_FILE}", file=sys.stderr)
    print("       Add one of:", file=sys.stderr)
    print("       OPENAI_API_KEY=sk-...", file=sys.stderr)
    print("       OPENROUTER_API_KEY=sk-or-v1-...", file=sys.stderr)
    sys.exit(1)

if _requested_provider and _requested_provider not in VALID_PROVIDERS:
    print("\033[31mError: AI_PROVIDER must be one of: openai, openrouter\033[0m", file=sys.stderr)
    sys.exit(1)


def _resolve_provider() -> str:
    if _requested_provider:
        if _requested_provider == "openai" and not _has_openai_key:
            print("\033[31mError: AI_PROVIDER=openai requires OPENAI_API_KEY\033[0m", file=sys.stderr)
            sys.exit(1)
        if _requested_provider == "openrouter" and not _has_openrouter_key:
            print("\033[31mError: AI_PROVIDER=openrouter requires OPENROUTER_API_KEY\033[0m", file=sys.stderr)
            sys.exit(1)
        return _requested_provider
    return "openai" if _has_openai_key else "openrouter"


AI_PROVIDER = _resolve_provider()
AI_API_KEY = OPENAI_API_KEY if AI_PROVIDER == "openai" else OPENROUTER_API_KEY
RESPONSES_API_ENDPOINT = RESPONSES_ENDPOINTS[AI_PROVIDER]

OPENROUTER_EXTRA_HEADERS = {}
if os.environ.get("OPENROUTER_HTTP_REFERER"):
    OPENROUTER_EXTRA_HEADERS["HTTP-Referer"] = os.environ["OPENROUTER_HTTP_REFERER"]
if os.environ.get("OPENROUTER_APP_NAME"):
    OPENROUTER_EXTRA_HEADERS["X-Title"] = os.environ["OPENROUTER_APP_NAME"]

EXTRA_API_HEADERS = OPENROUTER_EXTRA_HEADERS if AI_PROVIDER == "openrouter" else {}


def resolve_model_for_provider(model: str) -> str:
    """Prefix bare GPT model names with 'openai/' when using OpenRouter."""
    if not isinstance(model, str) or not model.strip():
        raise ValueError("Model must be a non-empty string")
    if AI_PROVIDER != "openrouter" or "/" in model:
        return model
    return f"openai/{model}" if model.startswith("gpt-") else model


def _normalize_openrouter_online_model(model: str) -> str:
    return model if model.endswith(OPENROUTER_ONLINE_SUFFIX) else f"{model}{OPENROUTER_ONLINE_SUFFIX}"


def _strip_openrouter_online_suffix(model: str) -> str:
    return model[: -len(OPENROUTER_ONLINE_SUFFIX)] if model.endswith(OPENROUTER_ONLINE_SUFFIX) else model


def _ensure_trimmed_string(value, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _normalize_web_search_config(web_search):
    if not web_search:
        return None
    if web_search is True:
        return {}
    if not isinstance(web_search, dict):
        raise ValueError("web_search must be either bool or a dict")
    if web_search.get("enabled") is False:
        return None

    config = {}

    if "searchContextSize" in web_search:
        size = _ensure_trimmed_string(web_search["searchContextSize"], "web_search.searchContextSize")
        if size not in VALID_OPENAI_SEARCH_CONTEXT_SIZES:
            raise ValueError('web_search.searchContextSize must be one of: "low", "medium", "high"')
        config["searchContextSize"] = size

    if "engine" in web_search:
        engine = _ensure_trimmed_string(web_search["engine"], "web_search.engine")
        if engine not in VALID_OPENROUTER_WEB_ENGINES:
            raise ValueError('web_search.engine must be one of: "native", "exa"')
        config["engine"] = engine

    if "maxResults" in web_search:
        if not isinstance(web_search["maxResults"], int) or web_search["maxResults"] <= 0:
            raise ValueError("web_search.maxResults must be a positive integer")
        config["maxResults"] = web_search["maxResults"]

    if "searchPrompt" in web_search:
        config["searchPrompt"] = _ensure_trimmed_string(web_search["searchPrompt"], "web_search.searchPrompt")

    return config


def _add_unique_tool(tools, tool):
    if not tools:
        return [tool]
    if any(t.get("type") == tool["type"] for t in tools):
        return tools
    return [*tools, tool]


def _merge_openrouter_plugins(plugins, plugin):
    if not plugins:
        return [plugin]
    for i, p in enumerate(plugins):
        if p.get("id") == plugin["id"]:
            merged = {**p, **plugin}
            return [merged if j == i else existing for j, existing in enumerate(plugins)]
    return [*plugins, plugin]


def build_responses_request(*, model, tools=None, plugins=None, web_search=False, **rest):
    """Build a Responses API request dict, injecting web search config as needed."""
    request = {"model": resolve_model_for_provider(model), **rest}

    if tools is not None:
        request["tools"] = tools
    if plugins is not None:
        request["plugins"] = plugins

    web_search_config = _normalize_web_search_config(web_search)
    if not web_search_config and web_search_config is not {}:
        return request

    if AI_PROVIDER == "openrouter":
        has_plugin_overrides = any(
            k in web_search_config for k in ("engine", "maxResults", "searchPrompt")
        )
        if not has_plugin_overrides:
            request["model"] = _normalize_openrouter_online_model(request["model"])
            return request

        request["model"] = _strip_openrouter_online_suffix(request["model"])
        plugin = {"id": "web"}
        if "engine" in web_search_config:
            plugin["engine"] = web_search_config["engine"]
        if "maxResults" in web_search_config:
            plugin["max_results"] = web_search_config["maxResults"]
        if "searchPrompt" in web_search_config:
            plugin["search_prompt"] = web_search_config["searchPrompt"]
        request["plugins"] = _merge_openrouter_plugins(request.get("plugins"), plugin)
        return request

    request["tools"] = _add_unique_tool(request.get("tools"), {"type": "web_search_preview"})
    if web_search_config.get("searchContextSize"):
        request["web_search_options"] = {"search_context_size": web_search_config["searchContextSize"]}

    return request
