"""Core Agent class — wraps a Claude model with tools, memory, and identity."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

import anthropic

from axon.memory import Memory
from axon.message import Handoff, Message, MessageRole
from axon.tools import ToolRegistry

_HANDOFF_TOOL_SPEC = {
    "name": "_axon_handoff",
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


class Agent:
    """An autonomous agent backed by a Claude model.

    Args:
        name: Unique identifier for this agent within a network.
        role: One-line description of what this agent does.
        system: Full system prompt. Defaults to a prompt derived from `role`.
        model: Claude model ID. Defaults to claude-opus-4-8.
        tools: ToolRegistry containing callable tools.
        peers: List of peer agent names this agent can hand off to.
        max_iterations: Max tool-call loops per run. Guards against infinite loops.
        memory_size: Max messages kept in short-term memory.
    """

    def __init__(
        self,
        name: str,
        role: str = "general assistant",
        system: str | None = None,
        model: str = "claude-opus-4-8",
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
        self._client = anthropic.Anthropic()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self, user_input: str) -> str:
        """Run a turn synchronously. Returns the final text response."""
        import asyncio
        return asyncio.run(self.arun(user_input))

    async def arun(self, user_input: str) -> str:
        """Run a turn asynchronously. Returns the final text response."""
        self.memory.add(Message.user(user_input, sender="user"))

        for _ in range(self.max_iterations):
            response = await self._call_api()
            stop_reason = response.stop_reason

            if stop_reason == "end_turn":
                text = self._extract_text(response)
                self.memory.add(Message.assistant(text, sender=self.name))
                return text

            if stop_reason == "tool_use":
                tool_results = await self._handle_tool_use(response)
                if isinstance(tool_results, Handoff):
                    raise HandoffSignal(tool_results)
                # tool results are appended to memory inside _handle_tool_use
                continue

            # unexpected stop reason
            break

        text = self._extract_text(response)
        self.memory.add(Message.assistant(text, sender=self.name))
        return text

    async def astream(self, user_input: str) -> AsyncIterator[str]:
        """Stream text tokens from a single turn (no tool use in streaming mode)."""
        self.memory.add(Message.user(user_input, sender="user"))
        full_text = ""

        async with self._client.messages.stream(
            model=self.model,
            max_tokens=8192,
            system=self._system,
            messages=self.memory.api_messages()[:-1],  # exclude the just-added user msg
            thinking={"type": "adaptive"},
        ) as stream:
            async for text in stream.text_stream:
                full_text += text
                yield text

        self.memory.add(Message.assistant(full_text, sender=self.name))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _call_api(self) -> anthropic.types.Message:
        tool_specs = self.tools.specs()
        if self.peers:
            tool_specs = [_HANDOFF_TOOL_SPEC] + tool_specs

        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 8192,
            "system": self._system,
            "messages": self.memory.api_messages(),
            "thinking": {"type": "adaptive"},
        }
        if tool_specs:
            kwargs["tools"] = tool_specs

        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._client.messages.create(**kwargs),
        )

    async def _handle_tool_use(
        self, response: anthropic.types.Message
    ) -> list[dict] | Handoff:
        # Append the assistant's tool-use turn to history
        assistant_turn = {"role": "assistant", "content": response.content}
        self.memory._history.append(
            Message(
                role=MessageRole.ASSISTANT,
                content=json.dumps([b.model_dump() for b in response.content]),
                sender=self.name,
                metadata={"raw_blocks": response.content},
            )
        )

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            if block.name == "_axon_handoff":
                return Handoff(
                    target_agent=block.input["target_agent"],
                    message=block.input["message"],
                )

            try:
                result = self.tools.call(block.name, block.input)
                result_str = json.dumps(result) if not isinstance(result, str) else result
                is_error = False
            except Exception as exc:
                result_str = f"Error: {exc}"
                is_error = True

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result_str,
                "is_error": is_error,
            })

        # Append tool results as a user turn
        self.memory._history.append(
            Message(
                role=MessageRole.USER,
                content=json.dumps(tool_results),
                sender="tool",
                metadata={"raw_tool_results": tool_results},
            )
        )
        return tool_results

    @staticmethod
    def _extract_text(response: anthropic.types.Message) -> str:
        parts = [b.text for b in response.content if hasattr(b, "text")]
        return "\n".join(parts)

    def __repr__(self) -> str:
        return f"Agent(name={self.name!r}, model={self.model!r}, tools={len(self.tools)})"


class HandoffSignal(Exception):
    """Internal signal raised when an agent issues a handoff."""
    def __init__(self, handoff: Handoff) -> None:
        self.handoff = handoff
        super().__init__(f"Handoff → {handoff.target_agent}")
