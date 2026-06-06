"""Message types for inter-agent communication."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    role: MessageRole
    content: str
    sender: str | None = None
    recipient: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    @classmethod
    def user(cls, content: str, sender: str | None = None, **meta: Any) -> Message:
        return cls(role=MessageRole.USER, content=content, sender=sender, metadata=meta)

    @classmethod
    def assistant(cls, content: str, sender: str | None = None, **meta: Any) -> Message:
        return cls(role=MessageRole.ASSISTANT, content=content, sender=sender, metadata=meta)


@dataclass
class Handoff:
    """Signal from one agent to hand control to another."""
    target_agent: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)
