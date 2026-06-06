"""Network topology — defines how agents are wired together."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from solarium.agent import Agent
    from solarium.blackboard import Blackboard


class Topology(StrEnum):
    STAR = "star"          # one hub agent routes to specialists
    PIPELINE = "pipeline"  # agents run in sequence, output → next input
    MESH = "mesh"          # any agent can hand off to any other


class Network:
    """A named collection of agents with a declared topology.

    Optionally attach a ``Blackboard`` to give all agents shared memory.

    Args:
        name: Label for this network.
        topology: How agents are wired for handoffs.
        blackboard: Optional shared knowledge store. When provided, every agent
                    added to this network gets ``blackboard_read`` and
                    ``blackboard_write`` tools injected automatically.
    """

    def __init__(
        self,
        name: str = "solarium-network",
        topology: Topology = Topology.STAR,
        blackboard: Blackboard | None = None,
    ) -> None:
        self.name = name
        self.topology = topology
        self.blackboard = blackboard
        self._agents: dict[str, Agent] = {}

    def add(self, agent: Agent) -> Network:
        self._agents[agent.name] = agent
        if self.blackboard is not None:
            agent._blackboard_specs = self.blackboard.make_tools(agent.name)
        self._rewire()
        return self

    def remove(self, name: str) -> None:
        self._agents.pop(name, None)
        self._rewire()

    def get(self, name: str) -> Agent:
        try:
            return self._agents[name]
        except KeyError as exc:
            raise KeyError(f"No agent named {name!r} in network {self.name!r}") from exc

    def agents(self) -> list[Agent]:
        return list(self._agents.values())

    def _rewire(self) -> None:
        names = list(self._agents.keys())
        if self.topology == Topology.MESH:
            for agent in self._agents.values():
                agent.peers = [n for n in names if n != agent.name]
        elif self.topology == Topology.STAR:
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
        agents = list(self._agents)
        board = f", blackboard={self.blackboard!r}" if self.blackboard else ""
        return f"Network({self.name!r}, topology={self.topology.value}, agents={agents}{board})"
