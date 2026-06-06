"""Orchestrator — drives multi-agent conversations and handles handoffs."""

from __future__ import annotations

import asyncio
from typing import Any

from axon.agent import Agent, HandoffSignal
from axon.message import Handoff
from axon.network import Network


class Orchestrator:
    """Runs a conversation across a network of agents.

    The orchestrator starts with a designated entry agent and follows
    handoff signals until an agent returns a final answer or the
    max_handoffs limit is reached.

    Args:
        network: The agent network to operate over.
        entry: Name of the agent that receives the initial user message.
               Defaults to the first agent added to the network.
        max_handoffs: Safety ceiling on the total number of handoffs.
    """

    def __init__(
        self,
        network: Network,
        entry: str | None = None,
        max_handoffs: int = 10,
    ) -> None:
        self.network = network
        self._entry = entry
        self.max_handoffs = max_handoffs

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self, user_input: str) -> str:
        return asyncio.run(self.arun(user_input))

    async def arun(self, user_input: str) -> str:
        agents = self.network.agents()
        if not agents:
            raise RuntimeError("Network has no agents.")

        entry_name = self._entry or agents[0].name
        current_agent = self.network.get(entry_name)
        current_input = user_input
        handoffs = 0

        while handoffs <= self.max_handoffs:
            try:
                result = await current_agent.arun(current_input)
                return result
            except HandoffSignal as hs:
                handoff: Handoff = hs.handoff
                handoffs += 1
                if handoffs > self.max_handoffs:
                    raise RuntimeError(
                        f"Max handoffs ({self.max_handoffs}) exceeded. "
                        f"Last agent: {current_agent.name}"
                    ) from hs
                current_agent = self.network.get(handoff.target_agent)
                current_input = handoff.message

        raise RuntimeError("Orchestrator loop exited unexpectedly.")

    async def arun_pipeline(self, user_input: str) -> list[tuple[str, str]]:
        """Run all agents in pipeline order, collecting (agent_name, output) pairs."""
        agents = self.network.agents()
        if not agents:
            raise RuntimeError("Network has no agents.")

        transcript: list[tuple[str, str]] = []
        current = user_input

        for agent in agents:
            output = await agent.arun(current)
            transcript.append((agent.name, output))
            current = output

        return transcript

    def __repr__(self) -> str:
        return (
            f"Orchestrator(network={self.network.name!r}, "
            f"entry={self._entry!r}, max_handoffs={self.max_handoffs})"
        )
