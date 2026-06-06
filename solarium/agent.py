"""Core Agent class — wraps a provider with tools, memory, and identity."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from solarium.memory import Memory
from solarium.message import Handoff
from solarium.providers.base import BaseProvider, ToolCall, ToolResult
from solarium.tools import ToolRegistry

_HANDOFF_TOOL_SPEC = {
    "name": "_solarium_handoff",
    "description": (
        "Hand off control to another agent. Use this when the task requires "
        "a different specialist. Provide the target agent's name and a clear message."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "target_agent": {"type": "string", "description": "Name of the agent to hand off to"},
            "message": {"type": "string", "description": "Message to pass to the target agent"},
        },
        "required": ["target_agent", "message"],
    },
}


def _make_default_provider(model: str, api_key: str | None) -> BaseProvider:
    from solarium.providers.anthropic_provider import AnthropicProvider
    p = AnthropicProvider(api_key=api_key)
    p._model = model  # type: ignore[attr-defined]
    return p


class Agent:
    """An autonomous agent backed by a configurable LLM provider.

    Args:
        name: Unique identifier within a network.
        role: One-line description used to auto-generate a system prompt.
        system: Full system prompt — overrides `role` if provided.
        model: Model ID string passed to the provider.
        provider: A ``BaseProvider`` instance. Defaults to Anthropic (claude-opus-4-8).
                  Pass an ``OpenAIProvider`` to use GPT-4o or any compatible endpoint.
        api_key: API key for the default Anthropic provider. Reads from env if omitted.
        tools: A ``ToolRegistry`` of callable tools.
        peers: Agent names this agent can hand off to.
        max_iterations: Max tool-call loops per turn.
        memory_size: Max messages in rolling history.

    Examples::

        # Anthropic (default)
        agent = Agent(name="bot", model="claude-opus-4-8")

        # OpenAI
        from solarium.providers import OpenAIProvider
        agent = Agent(name="bot", model="gpt-4o", provider=OpenAIProvider())

        # Groq (OpenAI-compatible)
        agent = Agent(
            name="bot",
            model="llama-3.1-70b-versatile",
            provider=OpenAIProvider(
                api_key="gsk_...",
                base_url="https://api.groq.com/openai/v1",
            ),
        )
    """

    def __init__(
        self,
        name: str,
        role: str = "general assistant",
        system: str | None = None,
        model: str = "claude-opus-4-8",
        provider: BaseProvider | None = None,
        api_key: str | None = None,
        tools: ToolRegistry | None = None,
        peers: list[str] | None = None,
        max_iterations: int = 20,
        memory_size: int = 100,
    ) -> None:
        self.name = name
        self.role = role
        self.model = model
        self.tools = tools or ToolRegistry()
        self.peers = peers or []
        self.max_iterations = max_iterations
        self.memory = Memory(max_messages=memory_size)

        self._system = system or f"You are {name}, a {role}. Be concise and accurate."
        self._provider = (
            provider if provider is not None else _make_default_provider(model, api_key)
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self, user_input: str) -> str:
        import asyncio
        return asyncio.run(self.arun(user_input))

    async def arun(self, user_input: str) -> str:
        self.memory.add_internal({"role": "user", "content": user_input})

        for _ in range(self.max_iterations):
            response = await self._provider.complete(
                system=self._system,
                history=self.memory.internal_messages(),
                tools=self._tool_specs(),
            )

            if response.stop_reason == "end_turn":
                self.memory.add_internal({"role": "assistant", "content": response.text})
                return response.text

            if response.stop_reason == "tool_use":
                for tc in response.tool_calls:
                    if tc.name == "_solarium_handoff":
                        raise HandoffSignal(Handoff(
                            target_agent=str(tc.input["target_agent"]),
                            message=str(tc.input["message"]),
                        ))

                self.memory.add_internal({
                    "role": "assistant",
                    "content": response.text,
                    "tool_calls": response.tool_calls,
                })
                results = self._execute_tools(response.tool_calls)
                self.memory.add_internal({"role": "tool_results", "results": results})
                continue

            break

        self.memory.add_internal({"role": "assistant", "content": response.text})
        return response.text

    async def astream(self, user_input: str) -> AsyncIterator[str]:
        """Stream a single-turn response (no tool use)."""
        self.memory.add_internal({"role": "user", "content": user_input})
        response = await self._provider.complete(
            system=self._system,
            history=self.memory.internal_messages(),
            tools=[],
        )
        self.memory.add_internal({"role": "assistant", "content": response.text})
        yield response.text

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _tool_specs(self) -> list[dict[str, Any]]:
        specs = self.tools.specs()
        if self.peers:
            specs = [_HANDOFF_TOOL_SPEC] + specs
        return specs

    def _execute_tools(self, tool_calls: list[ToolCall]) -> list[ToolResult]:
        results: list[ToolResult] = []
        for tc in tool_calls:
            try:
                raw = self.tools.call(tc.name, tc.input)
                content = json.dumps(raw) if not isinstance(raw, str) else raw
                results.append(ToolResult(id=tc.id, content=content))
            except Exception as exc:
                results.append(ToolResult(id=tc.id, content=f"Error: {exc}", is_error=True))
        return results

    def __repr__(self) -> str:
        return (
            f"Agent(name={self.name!r}, model={self.model!r}, "
            f"provider={type(self._provider).__name__})"
        )


class HandoffSignal(Exception):
    def __init__(self, handoff: Handoff) -> None:
        self.handoff = handoff
        super().__init__(f"Handoff → {handoff.target_agent}")
