"""Solarium — a multi-agent framework built on the Anthropic Claude API."""

from solarium.agent import Agent
from solarium.memory import Memory
from solarium.message import Handoff, Message, MessageRole
from solarium.network import Network, Topology
from solarium.orchestrator import Orchestrator
from solarium.tools import ToolRegistry, tool

__version__ = "0.1.0"
__all__ = [
    "Agent",
    "Orchestrator",
    "Message",
    "MessageRole",
    "Handoff",
    "tool",
    "ToolRegistry",
    "Memory",
    "Network",
    "Topology",
]
