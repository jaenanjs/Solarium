"""Anthropic Claude provider."""

from __future__ import annotations

import asyncio
from typing import Any

import anthropic

from solarium.providers.base import (
    BaseProvider,
    CompletionResponse,
    InternalMessage,
    ToolCall,
)


class AnthropicProvider(BaseProvider):
    def __init__(self, api_key: str | None = None) -> None:
        self._client = anthropic.Anthropic(api_key=api_key)

    def supports_thinking(self) -> bool:
        return True

    async def complete(
        self,
        system: str,
        history: list[InternalMessage],
        tools: list[dict[str, Any]],
    ) -> CompletionResponse:
        messages = self._convert_history(history)
        kwargs: dict[str, Any] = {
            "model": "claude-opus-4-8",  # overridden by Agent
            "max_tokens": 8192,
            "system": system,
            "messages": messages,
            "thinking": {"type": "adaptive"},
        }
        if tools:
            kwargs["tools"] = tools

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self._client.messages.create(**kwargs),
        )

        text = "\n".join(b.text for b in response.content if hasattr(b, "text"))
        tool_calls = [
            ToolCall(id=b.id, name=b.name, input=dict(b.input))
            for b in response.content
            if b.type == "tool_use"
        ]
        stop_reason = "tool_use" if tool_calls else "end_turn"
        return CompletionResponse(text=text, stop_reason=stop_reason, tool_calls=tool_calls)

    def _convert_history(self, history: list[InternalMessage]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for msg in history:
            role = msg["role"]
            if role in ("user", "assistant") and "tool_calls" not in msg:
                out.append({"role": role, "content": msg["content"]})
            elif role == "assistant" and "tool_calls" in msg:
                content: list[dict[str, Any]] = []
                if msg.get("content"):
                    content.append({"type": "text", "text": msg["content"]})
                for tc in msg["tool_calls"]:
                    content.append({
                        "type": "tool_use",
                        "id": tc.id,
                        "name": tc.name,
                        "input": tc.input,
                    })
                out.append({"role": "assistant", "content": content})
            elif role == "tool_results":
                content = [
                    {
                        "type": "tool_result",
                        "tool_use_id": r.id,
                        "content": r.content,
                        "is_error": r.is_error,
                    }
                    for r in msg["results"]
                ]
                out.append({"role": "user", "content": content})
        return out


def make_anthropic_provider(model: str, api_key: str | None = None) -> AnthropicProvider:
    """Return an AnthropicProvider pre-configured with the given model."""
    provider = AnthropicProvider(api_key=api_key)
    provider._model = model  # type: ignore[attr-defined]
    return provider
