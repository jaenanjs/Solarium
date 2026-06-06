# Solarium

**A multi-agent framework built on the Anthropic Claude API.**

Solarium lets you build networks of AI agents that collaborate, delegate tasks to specialists, and maintain memory across conversations — all with a clean Python API.

---

## Install

```bash
pip install solarium
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Core concepts

| Concept | What it does |
|---|---|
| [`Agent`](agents.md) | A Claude-backed agent with tools, memory, and a system prompt |
| [`ToolRegistry`](tools.md) | Register Python functions as callable tools |
| [`Network`](network.md) | Wire agents together with a topology |
| [`Orchestrator`](orchestrator.md) | Drive multi-agent conversations end-to-end |
| [`Memory`](memory.md) | Per-agent rolling history and key-value store |

---

## Quickstart

```python
import solarium

agent = solarium.Agent(name="assistant", role="helpful AI assistant")
print(agent.run("Explain quantum entanglement in one sentence."))
```

---

## Guides

- [Building your first agent](guides/first-agent.md)
- [Adding tools](guides/tools.md)
- [Multi-agent networks](guides/networks.md)
- [Streaming responses](guides/streaming.md)
