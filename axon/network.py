"""Network topology — defines how agents are wired together."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from axon.agent import Agent


class Topology(str, Enum):
    STAR = "star"        # one hub agent routes to specialists
    PIPELINE = "pipeline"  # agents run in sequence, output → next input
    MESH = "mesh"        # any agent can hand off to any other


class Network:
    """A named collection of agents with a declared topology.

    The network wires peer lists based on topology so agents can issue handoffs
    without manually specifying every connection.
    """

    def __init__(self, name: str = "axon-network", topology: Topology = Topology.STAR) -> None:
        self.name = name
        self.topology = topology
        self._agents: dict[str, "Agent"] = {}

    def add(self, agent: "Agent") -> "Network":
        self._agents[agent.name] = agent
        self._rewire()
        return self

    def remove(self, name: str) -> None:
        self._agents.pop(name, None)
        self._rewire()

    def get(self, name: str) -> "Agent":
        try:
            return self._agents[name]
        except KeyError:
            raise KeyError(f"No agent named {name!r} in network {self.name!r}")

    def agents(self) -> list["Agent"]:
        return list(self._agents.values())

    def _rewire(self) -> None:
        names = list(self._agents.keys())
        if self.topology == Topology.MESH:
            for agent in self._agents.values():
                agent.peers = [n for n in names if n != agent.name]
        elif self.topology == Topology.STAR:
            # First agent added becomes the hub; it can reach all others.
            # Spoke agents can only reach the hub.
            if not names:
                return
            hub = names[0]
            spokes = names[1:]
            self._agents[hub].peers = spokes
            for spoke in spokes:
                self._agents[spoke].peers = [hub]
        elif self.topology == Topology.PIPELINE:
            for i, name in enumerate(names):
                self._agents[name].peers = [names[i + 1]] if i + 1 < len(names) else []

    def __repr__(self) -> str:
        return f"Network({self.name!r}, topology={self.topology.value}, agents={list(self._agents)})"
