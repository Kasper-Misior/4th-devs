"""
Sampling handler — mirrors src/sampling.js.

Bridges MCP sampling/createMessage requests to the AI provider so the server
can ask the client to run an LLM completion without needing its own API key.
"""

from src.ai import completion
from src.log import client_log


def create_sampling_handler(model: str):
    """Return an async handler for sampling/createMessage requests."""

    async def handler(request) -> dict:
        params = request.params
        client_log.sampling_request({"messages": params.messages, "maxTokens": params.maxTokens})

        try:
            # Convert MCP message objects → plain dicts for the Responses API
            input_messages = [
                {
                    "role": msg.role,
                    "content": msg.content.text if msg.content.type == "text" else str(msg.content),
                }
                for msg in params.messages
            ]

            text = completion(
                model=model,
                input_messages=input_messages,
                max_output_tokens=params.maxTokens or 500,
            )
            client_log.sampling_response(text)

            from mcp.types import CreateMessageResult, TextContent
            return CreateMessageResult(
                role="assistant",
                content=TextContent(type="text", text=text),
                model=model,
            )
        except Exception as e:
            client_log.sampling_error(e)
            raise

    return handler
