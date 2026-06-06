# Memory

Every agent has a `Memory` instance at `agent.memory`. It handles two things: rolling conversation history and a long-term key-value store.

## Conversation history

Messages are automatically added during `agent.run()` / `agent.arun()`. The history is sent to Claude on every turn so agents remember prior context.

```python
agent.run("My name is Alice.")
agent.run("What's my name?")  # → "Your name is Alice."
```

History rolls over at `memory_size` messages (default 100) — the oldest messages are dropped first.

### Manual access

```python
agent.memory.messages()       # list of Message objects
agent.memory.api_messages()   # list of dicts in Claude API format
agent.memory.clear_history()  # wipe conversation history
```

## Key-value store

Store arbitrary data that persists across the agent's lifetime.

```python
agent.memory.remember("user_id", "user_abc123")
agent.memory.remember("preferences", {"language": "en", "tone": "formal"})

agent.memory.recall("user_id")           # → "user_abc123"
agent.memory.recall("missing", default="n/a")  # → "n/a"

agent.memory.forget("user_id")
agent.memory.snapshot()  # → dict of all stored keys
```

## Memory across agents

Each agent has its own isolated memory. To share state between agents, pass data explicitly through tool results or handoff messages, or use a shared external store via a tool.

## API reference

| Method | Description |
|---|---|
| `add(message)` | Append a `Message` to history |
| `messages()` | Return full history as `list[Message]` |
| `api_messages()` | Return history formatted for the Claude API |
| `clear_history()` | Clear conversation history |
| `remember(key, value)` | Store a value in the KV store |
| `recall(key, default)` | Retrieve a value by key |
| `forget(key)` | Remove a key from the KV store |
| `snapshot()` | Return a copy of the entire KV store |
