"""Tests for Network topology wiring."""

from unittest.mock import MagicMock

import pytest

from solarium.network import Network, Topology


def make_agent(name: str):
    agent = MagicMock()
    agent.name = name
    agent.peers = []
    return agent


def test_star_wiring():
    net = Network(topology=Topology.STAR)
    hub = make_agent("hub")
    a = make_agent("a")
    b = make_agent("b")
    net.add(hub)
    net.add(a)
    net.add(b)
    assert set(hub.peers) == {"a", "b"}
    assert a.peers == ["hub"]
    assert b.peers == ["hub"]


def test_mesh_wiring():
    net = Network(topology=Topology.MESH)
    agents = [make_agent(n) for n in ["x", "y", "z"]]
    for ag in agents:
        net.add(ag)
    for ag in agents:
        others = {a.name for a in agents if a.name != ag.name}
        assert set(ag.peers) == others


def test_pipeline_wiring():
    net = Network(topology=Topology.PIPELINE)
    a, b, c = make_agent("a"), make_agent("b"), make_agent("c")
    net.add(a)
    net.add(b)
    net.add(c)
    assert a.peers == ["b"]
    assert b.peers == ["c"]
    assert c.peers == []


def test_get_unknown_agent_raises():
    net = Network()
    with pytest.raises(KeyError):
        net.get("nobody")
