"""Abstract base provider and shared data types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict[str, Any]


@dataclass
class ToolResult:
    id: str
    content: str
    is_error: bool = False


@dataclass
class CompletionResponse:
    text: str
    stop_reason: str          # "end_turn" | "tool_use"
    tool_calls: list[ToolCall] = field(default_factory=list)


# Internal message format stored in Memory.
# Regular turn:      {"role": "user"|"assistant", "content": str}
# Tool-use turn:     {"role": "assistant", "content": str, "tool_calls": [ToolCall]}
# Tool-result turn:  {"role": "tool_results", "results": [ToolResult]}
InternalMessage = dict[str, Any]


class BaseProvider(ABC):
    """Interface every provider must implement."""

    @abstractmethod
    async def complete(
        self,
        system: str,
        history: list[InternalMessage],
        tools: list[dict[str, Any]],
    ) -> CompletionResponse: ...

    @abstractmethod
    def supports_thinking(self) -> bool: ...
