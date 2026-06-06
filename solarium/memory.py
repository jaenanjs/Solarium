"""Agent memory — short-term conversation history and long-term key-value store."""

from __future__ import annotations

from collections import deque
from typing import Any

from solarium.providers.base import InternalMessage


class Memory:
    def __init__(self, max_messages: int = 100):
        self._history: deque[InternalMessage] = deque(maxlen=max_messages)
        self._store: dict[str, Any] = {}

    # --- conversation history ---

    def add_internal(self, msg: InternalMessage) -> None:
        self._history.append(msg)

    def internal_messages(self) -> list[InternalMessage]:
        return list(self._history)

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
