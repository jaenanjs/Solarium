"""Agent memory — short-term conversation history and long-term key-value store."""

from __future__ import annotations

from collections import deque
from typing import Any

from anthropic.types import MessageParam

from solarium.message import Message, MessageRole


class Memory:
    def __init__(self, max_messages: int = 100):
        self._history: deque[Message] = deque(maxlen=max_messages)
        self._store: dict[str, Any] = {}

    # --- conversation history ---

    def add(self, message: Message) -> None:
        self._history.append(message)

    def messages(self) -> list[Message]:
        return list(self._history)

    def api_messages(self) -> list[MessageParam]:
        """Return history in the format expected by the Claude Messages API."""
        out: list[MessageParam] = []
        for msg in self._history:
            if msg.role in (MessageRole.USER, MessageRole.ASSISTANT):
                out.append(msg.to_api())
        return out

    def clear_history(self) -> None:
        self._history.clear()

    # --- long-term key-value store ---

    def remember(self, key: str, value: Any) -> None:
        self._store[key] = value

    def recall(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def forget(self, key: str) -> None:
        self._store.pop(key, None)

    def snapshot(self) -> dict[str, Any]:
        return dict(self._store)
