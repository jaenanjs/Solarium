# Agent

The `Agent` class is the core building block of Solarium. Each agent wraps a Claude model with a persistent memory, an optional set of tools, and a system prompt that defines its role.

## Constructor

```python
solarium.Agent(
    name: str,
    role: str = "general assistant",
    system: str | None = None,
    model: str = "claude-opus-4-8",
    tools: ToolRegistry | None = None,
    peers: list[str] | None = None,
    max_iterations: int = 20,
    memory_size: int = 100,
)
```

| Parameter | Description |
|---|---|
| `name` | Unique identifier within a network |
| `role` | One-line description used to auto-generate a system prompt |
| `system` | Full system prompt — overrides `role` if provided |
| `model` | Claude model ID. Defaults to `claude-opus-4-8` |
| `tools` | A `ToolRegistry` of callable tools |
| `peers` | Agent names this agent can hand off to |
| `max_iterations` | Max tool-call loops per turn (prevents infinite loops) |
| `memory_size` | Max messages in rolling conversation history |

## Methods

### `run(user_input) → str`
Synchronous. Runs one turn and returns the final text response.

```python
answer = agent.run("What is the capital of France?")
```

### `await arun(user_input) → str`
Async version of `run`.

```python
answer = await agent.arun("What is the capital of France?")
```

### `await astream(user_input) → AsyncIterator[str]`
Stream tokens as they arrive.

```python
async for token in agent.astream("Tell me a story."):
    print(token, end="", flush=True)
```

## Memory

Every agent has a `memory` attribute (`Memory` instance) that persists across turns.

```python
agent.run("My name is Alice.")
agent.run("What is my name?")  # → "Your name is Alice."

# Long-term key-value store
agent.memory.remember("user_tier", "premium")
agent.memory.recall("user_tier")  # → "premium"
```

## Adaptive thinking

All agents use `thinking: {type: "adaptive"}` by default — Claude decides how much internal reasoning to apply based on the complexity of each request.

## Example

```python
import solarium

@solarium.tool
def get_weather(city: str) -> str:
    """Return the current weather for a city."""
    return f"72°F and sunny in {city}."

registry = solarium.ToolRegistry()
registry.register(get_weather)

agent = solarium.Agent(
    name="weather-bot",
    role="weather assistant",
    tools=registry,
)

print(agent.run("What's the weather in Tokyo?"))
```
