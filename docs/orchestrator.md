# Orchestrator

The `Orchestrator` drives conversations across a `Network`, automatically following handoff signals between agents until a final answer is returned.

## Constructor

```python
solarium.Orchestrator(
    network: Network,
    entry: str | None = None,   # name of the first agent to receive input
    max_handoffs: int = 10,     # safety ceiling on total handoffs
)
```

If `entry` is omitted, the first agent added to the network receives the initial message.

## Methods

### `run(user_input) → str`
Synchronous. Runs the full multi-agent conversation and returns the final answer.

```python
result = orchestrator.run("Explain how neural networks learn.")
```

### `await arun(user_input) → str`
Async version of `run`.

```python
result = await orchestrator.arun("Explain how neural networks learn.")
```

### `await arun_pipeline(user_input) → list[tuple[str, str]]`
For `PIPELINE` topology. Runs all agents in sequence and returns every `(agent_name, output)` pair.

```python
transcript = await orchestrator.arun_pipeline("climate change")
for agent_name, output in transcript:
    print(f"\n=== {agent_name} ===\n{output}")
```

## How it works

```
user_input
    │
    ▼
entry agent ──► [tool calls] ──► answer?  ──► return
                     │
                  handoff?
                     │
                     ▼
              target agent ──► [tool calls] ──► answer?  ──► return
```

1. The entry agent receives `user_input` and runs its agentic loop
2. If it returns text → that's the final answer
3. If it issues a handoff → the orchestrator routes to the target agent with the handoff message
4. Repeats until an agent returns text or `max_handoffs` is exceeded

## Example

```python
import solarium
from solarium.network import Topology

network = solarium.Network(topology=Topology.STAR)

router = solarium.Agent(
    name="router",
    system=(
        "You route tasks. Hand off to 'analyst' for data questions "
        "or 'writer' for content creation. Use _solarium_handoff."
    ),
)
analyst = solarium.Agent(name="analyst", role="data analyst")
writer = solarium.Agent(name="writer", role="creative writer")

network.add(router).add(analyst).add(writer)

orchestrator = solarium.Orchestrator(network, entry="router", max_handoffs=5)
print(orchestrator.run("Write a blog post about large language models."))
```
