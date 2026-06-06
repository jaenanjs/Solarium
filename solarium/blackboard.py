"""Blackboard — a shared knowledge store for all agents in a network.

Classic AI architecture (Hearsay-II, 1977) adapted for LLM multi-agent systems.
Every agent attached to a network with a Blackboard gets read/write tool access
automatically. Agents can leave findings, coordinate on shared state, and react
to each other's contributions without explicit handoffs.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class BlackboardEntry:
    key: str
    value: Any
    author: str
    note: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "author": self.author,
            "note": self.note,
            "timestamp": self.timestamp.isoformat(),
        }


class Blackboard:
    """Shared knowledge store that all agents in a network can read and write.

    Thread-safe. Keeps a full audit trail of every write.

    Usage::

        board = Blackboard()
        network = Network(topology=Topology.MESH, blackboard=board)
        network.add(researcher).add(analyst)
        # Both agents now have blackboard_read / blackboard_write tools injected.

        # Programmatic access
        board.write("findings", "LLMs work by...", author="researcher")
        board.read("findings")
        board.history("findings")   # full audit trail
        board.snapshot()            # all current values
    """

    def __init__(self) -> None:
        self._store: dict[str, Any] = {}
        self._history: dict[str, list[BlackboardEntry]] = {}
        self._watchers: dict[str, list[Callable[[BlackboardEntry], None]]] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def write(self, key: str, value: Any, author: str = "unknown", note: str = "") -> None:
        """Write a value to the blackboard and notify any watchers."""
        entry = BlackboardEntry(key=key, value=value, author=author, note=note)
        with self._lock:
            self._store[key] = value
            self._history.setdefault(key, []).append(entry)
            watchers = list(self._watchers.get(key, []))

        for callback in watchers:
            try:
                callback(entry)
            except Exception:
                pass

    def read(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._store.get(key, default)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def keys(self) -> list[str]:
        with self._lock:
            return list(self._store.keys())

    def snapshot(self) -> dict[str, Any]:
        """Return a copy of the entire current state."""
        with self._lock:
            return dict(self._store)

    # ------------------------------------------------------------------
    # History & audit
    # ------------------------------------------------------------------

    def history(self, key: str) -> list[BlackboardEntry]:
        """Return all writes to a key in chronological order."""
        with self._lock:
            return list(self._history.get(key, []))

    def full_history(self) -> list[BlackboardEntry]:
        """Return every write across all keys, sorted by timestamp."""
        with self._lock:
            all_entries = [e for entries in self._history.values() for e in entries]
        return sorted(all_entries, key=lambda e: e.timestamp)

    def last_author(self, key: str) -> str | None:
        """Return the name of the agent that last wrote to a key."""
        entries = self.history(key)
        return entries[-1].author if entries else None

    # ------------------------------------------------------------------
    # Reactive watching
    # ------------------------------------------------------------------

    def watch(self, key: str, callback: Callable[[BlackboardEntry], None]) -> None:
        """Call `callback(entry)` every time `key` is written."""
        with self._lock:
            self._watchers.setdefault(key, []).append(callback)

    def unwatch(self, key: str, callback: Callable[[BlackboardEntry], None]) -> None:
        with self._lock:
            watchers = self._watchers.get(key, [])
            if callback in watchers:
                watchers.remove(callback)

    # ------------------------------------------------------------------
    # Tool factory — called by Network when wiring agents
    # ------------------------------------------------------------------

    def make_tools(self, agent_name: str) -> list[dict[str, Any]]:
        """Return tool specs for blackboard_read and blackboard_write."""
        return [
            {
                "name": "blackboard_read",
                "description": (
                    "Read a value from the shared blackboard. "
                    "Use this to access findings or state left by other agents."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "The key to read"},
                    },
                    "required": ["key"],
                },
                "_handler": lambda key, _author=agent_name: self._handle_read(key),
            },
            {
                "name": "blackboard_write",
                "description": (
                    "Write a value to the shared blackboard so other agents can read it. "
                    "Use this to share findings, results, or intermediate state."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "key": {"type": "string", "description": "Key to write"},
                        "value": {"type": "string", "description": "Value to store"},
                        "note": {
                            "type": "string",
                            "description": "Optional note explaining why you wrote this",
                        },
                    },
                    "required": ["key", "value"],
                },
                "_handler": lambda key, value, note="", _author=agent_name: (
                    self._handle_write(key, value, _author, note)
                ),
            },
        ]

    def _handle_read(self, key: str) -> str:
        value = self.read(key)
        if value is None:
            known = self.keys()
            hint = f" Known keys: {known}" if known else " The blackboard is empty."
            return f"Key '{key}' not found.{hint}"
        return json.dumps(value) if not isinstance(value, str) else value

    def _handle_write(self, key: str, value: str, author: str, note: str) -> str:
        self.write(key, value, author=author, note=note)
        return f"Written '{key}' to blackboard."

    def __repr__(self) -> str:
        return f"Blackboard(keys={self.keys()})"
