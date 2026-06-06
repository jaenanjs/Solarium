"""OpenAI-compatible provider (OpenAI, Groq, Together, Ollama, etc.)."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from solarium.providers.base import (
    BaseProvider,
    CompletionResponse,
    InternalMessage,
    ToolCall,
)


class OpenAIProvider(BaseProvider):
    """Works with any OpenAI-compatible API endpoint.

    Args:
        api_key: API key. Reads OPENAI_API_KEY env var if not provided.
        base_url: Override the base URL for compatible providers
                  (e.g. Groq, Together, Ollama, Azure OpenAI).
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError(
                "openai package is required for OpenAIProvider. "
                "Install it with: pip install solarium[openai]"
            ) from exc

        kwargs: dict[str, Any] = {}
        if api_key:
            kwargs["api_key"] = api_key
        if base_url:
            kwargs["base_url"] = base_url

        from openai import OpenAI
        self._client = OpenAI(**kwargs)

    def supports_thinking(self) -> bool:
        return False

    async def complete(
        self,
        system: str,
        history: list[InternalMessage],
        tools: list[dict[str, Any]],
    ) -> CompletionResponse:
        messages = self._convert_history(system, history)
        kwargs: dict[str, Any] = {"model": "gpt-4o", "messages": messages}
        if tools:
            kwargs["tools"] = self._convert_tools(tools)
            kwargs["tool_choice"] = "auto"

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self._client.chat.completions.create(**kwargs),
        )

        choice = response.choices[0]
        msg = choice.message
        text = msg.content or ""
        tool_calls: list[ToolCall] = []

        if msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    input=json.loads(tc.function.arguments),
                ))

        stop_reason = "tool_use" if tool_calls else "end_turn"
        return CompletionResponse(text=text, stop_reason=stop_reason, tool_calls=tool_calls)

    def _convert_history(
        self, system: str, history: list[InternalMessage]
    ) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = [{"role": "system", "content": system}]
        for msg in history:
            role = msg["role"]
            if role in ("user", "assistant") and "tool_calls" not in msg:
                out.append({"role": role, "content": msg["content"]})
            elif role == "assistant" and "tool_calls" in msg:
                out.append({
                    "role": "assistant",
                    "content": msg.get("content") or None,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.input),
                            },
                        }
                        for tc in msg["tool_calls"]
                    ],
                })
            elif role == "tool_results":
                for r in msg["results"]:
                    out.append({
                        "role": "tool",
                        "tool_call_id": r.id,
                        "content": r.content,
                    })
        return out

    @staticmethod
    def _convert_tools(specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert Solarium tool specs to OpenAI function-calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": spec["name"],
                    "description": spec["description"],
                    "parameters": spec["input_schema"],
                },
            }
            for spec in specs
        ]
