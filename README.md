# Solarium

**A multi-agent framework built on the Anthropic Claude API.**

Solarium models agents as neurons and messages as the signals that travel between them — giving you a clean, composable system for building networks of AI agents that collaborate, hand off tasks, and remember context.

---

## Features

- **`Agent`** — a Claude-backed agent with tools, memory, and adaptive thinking
- **`ToolRegistry`** + **`@tool` decorator** — define Python functions as tools with auto-generated JSON schemas
- **`Network`** — wire agents into topologies: `STAR`, `PIPELINE`, or `MESH`
- **`Orchestrator`** — drives conversations across a network, following handoffs automatically
- **`Memory`** — rolling conversation history + long-term key-value store per agent
- Streaming support via `agent.astream()`
- Async-first with `asyncio`; sync wrappers for quick scripts

---

## Quickstart

```bash
pip install solarium
export ANTHROPIC_API_KEY=sk-ant-...
```

### Single agent with a tool

```python
import solarium

@solarium.tool
def calculator(expression: str) -> str:
    """Evaluate an arithmetic expression."""
    return str(eval(expression))

registry = solarium.ToolRegistry()
registry.register(calculator)

agent = solarium.Agent(name="math", role="arithmetic assistant", tools=registry)
print(agent.run("What is 12 * (3 + 7)?"))
```

### Multi-agent with handoffs (star topology)

```python
import solarium
from solarium.network import Topology

network = solarium.Network(topology=Topology.STAR)

router = solarium.Agent(
    name="router",
    role="task router",
    system="Analyze the task and hand off to 'researcher' or 'coder'. Use _solarium_handoff.",
)
researcher = solarium.Agent(name="researcher", role="research specialist")
coder = solarium.Agent(name="coder", role="Python coding specialist")

network.add(router).add(researcher).add(coder)

orchestrator = solarium.Orchestrator(network, entry="router")
print(orchestrator.run("Write a Python function that reverses a string."))
```

### Pipeline

```python
import solarium
from solarium.network import Topology

network = solarium.Network(topology=Topology.PIPELINE)
network.add(solarium.Agent(name="drafter", role="first-draft writer"))
network.add(solarium.Agent(name="editor", role="copy editor"))

orchestrator = solarium.Orchestrator(network)
import asyncio
transcript = asyncio.run(orchestrator.arun_pipeline("renewable energy"))
for name, output in transcript:
    print(f"\n=== {name} ===\n{output}")
```

### Streaming

```python
import asyncio, solarium

agent = solarium.Agent(name="poet", role="creative writer")

async def main():
    async for token in agent.astream("Write a haiku about code."):
        print(token, end="", flush=True)

asyncio.run(main())
```

---

## Architecture

```
solarium/
├── agent.py        # Agent — Claude + tools + memory + handoff support
├── orchestrator.py # Orchestrator — drives multi-agent loops
├── network.py      # Network + Topology — wires agents together
├── memory.py       # Memory — rolling history + KV store
├── tools.py        # @tool decorator + ToolRegistry
├── message.py      # Message, MessageRole, Handoff
└── exceptions.py   # Framework exceptions
```

---

## Models

Solarium defaults to `claude-opus-4-8` with adaptive thinking enabled. Override per-agent:

```python
agent = solarium.Agent(name="fast", model="claude-haiku-4-5")
```

---

## Development

```bash
git clone https://github.com/jaenan/solarium
cd solarium
pip install -e ".[dev]"
pytest
ruff check solarium tests
mypy solarium
```

---

## License

MIT
