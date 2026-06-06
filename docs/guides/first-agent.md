# Building your first agent

This guide walks you through creating a single agent, giving it a tool, and running it.

## 1. Install Solarium

```bash
pip install solarium
export ANTHROPIC_API_KEY=sk-ant-...
```

## 2. Create an agent

The simplest possible agent — no tools, just a Claude model with a role:

```python
import solarium

agent = solarium.Agent(
    name="assistant",
    role="helpful AI assistant",
)

response = agent.run("What's the boiling point of water in Fahrenheit?")
print(response)
```

## 3. Give it a tool

Tools let the agent take actions in the world. Decorate any Python function with `@solarium.tool`:

```python
import solarium

@solarium.tool
def get_stock_price(ticker: str) -> str:
    """Get the current stock price for a ticker symbol."""
    # Replace with a real API call
    prices = {"AAPL": "189.42", "TSLA": "248.50", "NVDA": "875.10"}
    return prices.get(ticker.upper(), "Ticker not found.")

registry = solarium.ToolRegistry()
registry.register(get_stock_price)

agent = solarium.Agent(
    name="finance-bot",
    role="financial data assistant",
    tools=registry,
)

print(agent.run("What's the current price of Apple stock?"))
```

## 4. Have a multi-turn conversation

Agents remember conversation history automatically:

```python
agent = solarium.Agent(name="tutor", role="patient math tutor")

agent.run("I'm studying for a calculus exam.")
agent.run("Can you explain derivatives?")
response = agent.run("Give me a practice problem based on what we just discussed.")
print(response)
```

## 5. Use a custom system prompt

For full control, write your own system prompt:

```python
agent = solarium.Agent(
    name="chef",
    system=(
        "You are a world-class French chef. You speak with passion about food, "
        "occasionally use French phrases, and always recommend seasonal ingredients. "
        "Keep responses under 3 sentences."
    ),
)

print(agent.run("What should I cook for a dinner party this weekend?"))
```

## Next steps

- [Adding tools](tools.md) — deeper dive into tool definitions
- [Multi-agent networks](networks.md) — coordinate multiple specialists
- [Streaming responses](streaming.md) — stream tokens in real time
