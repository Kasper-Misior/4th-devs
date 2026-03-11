"""
Elicitation handler — mirrors src/elicitation.js.

Auto-accepts every elicitation form by inferring defaults from the JSON Schema.
"""

from src.log import client_log


def _infer_default(prop: dict):
    if "default" in prop:
        return prop["default"]
    if prop.get("type") == "boolean":
        return True
    enum = prop.get("enum")
    if enum:
        return enum[0]
    return None


def _auto_fill_defaults(schema: dict) -> dict:
    properties = schema.get("properties", {}) if schema else {}
    result = {}
    for key, prop in properties.items():
        value = _infer_default(prop)
        if value is not None:
            result[key] = value
    return result


def create_elicitation_handler(on_elicitation=None):
    """Return an async handler for elicitation/create requests."""

    async def handler(request) -> dict:
        params = request.params
        client_log.elicitation_request({"mode": getattr(params, "mode", "unknown")})

        if getattr(params, "mode", None) != "form":
            return {"action": "decline"}

        if callable(on_elicitation):
            return on_elicitation(params)

        # Demo mode: auto-fill from schema defaults
        schema = getattr(params, "requestedSchema", None)
        schema_dict = schema if isinstance(schema, dict) else (schema.model_dump() if schema else {})
        content = _auto_fill_defaults(schema_dict)
        client_log.auto_accepted_elicitation(content)

        return {"action": "accept", "content": content}

    return handler
