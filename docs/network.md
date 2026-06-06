# Network & Topology

A `Network` holds a named collection of agents and wires their `peers` lists based on a chosen topology. The topology determines which agents can hand off to which.

## Topologies

### STAR
One hub agent routes to any number of specialist spokes. Spokes can only return to the hub.

```
        ┌──────────┐
   ┌────┤   hub    ├────┐
   │    └──────────┘    │
   ▼                    ▼
researcher            coder
```

```python
from solarium.network import Topology

network = solarium.Network(topology=Topology.STAR)
network.add(hub).add(researcher).add(coder)
# hub.peers = ["researcher", "coder"]
# researcher.peers = ["hub"]
# coder.peers = ["hub"]
```

### PIPELINE
Each agent passes output to the next. No backtracking.

```
drafter ──► editor ──► critic
```

```python
network = solarium.Network(topology=Topology.PIPELINE)
network.add(drafter).add(editor).add(critic)
# drafter.peers = ["editor"]
# editor.peers = ["critic"]
# critic.peers = []
```

Use `orchestrator.arun_pipeline()` to collect each agent's output as a list.

### MESH
Every agent can hand off to any other agent.

```python
network = solarium.Network(topology=Topology.MESH)
network.add(agent_a).add(agent_b).add(agent_c)
# each agent's peers = all other agents
```

## API

```python
network = solarium.Network(
    name="my-network",       # optional label
    topology=Topology.STAR,  # STAR | PIPELINE | MESH
)

network.add(agent)       # add an agent (returns self for chaining)
network.remove("name")   # remove an agent by name
network.get("name")      # retrieve an agent by name
network.agents()         # list all agents
```

## Handoffs

Agents hand off by calling the internal `_solarium_handoff` tool, which is automatically injected when an agent has peers. Claude uses it when it determines the task is better handled by another agent.

The `Orchestrator` catches the handoff signal and routes the conversation to the target agent automatically.
