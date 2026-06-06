# Tools

Tools let agents call Python functions. Solarium auto-generates the JSON schema Claude needs from your function's type hints and docstring — no boilerplate required.

## Defining a tool

```python
import solarium

@solarium.tool
def search_web(query: str) -> str:
    """Search the web and return a summary of results."""
    # your implementation here
    return f"Results for: {query}"
```

The decorator reads:
- **Parameter names and types** → JSON schema properties
- **Docstring** → tool description shown to Claude
- **Function name** → tool name (overridable)

### Custom name and description

```python
@solarium.tool(name="web_search", description="Search the internet for current information.")
def search(query: str) -> str:
    ...
```

## Supported types

| Python type | JSON Schema type |
|---|---|
| `str` | `string` |
| `int` | `integer` |
| `float` | `number` |
| `bool` | `boolean` |
| `list` | `array` |
| `dict` | `object` |

## ToolRegistry

Register tools and attach them to an agent.

```python
registry = solarium.ToolRegistry()
registry.register(search_web)
registry.register_all(tool_a, tool_b, tool_c)

agent = solarium.Agent(name="researcher", tools=registry)
```

### Methods

| Method | Description |
|---|---|
| `register(fn)` | Register a single `@tool`-decorated function |
| `register_all(*fns)` | Register multiple functions at once |
| `specs()` | Return raw JSON schemas (passed to Claude API) |
| `call(name, inputs)` | Invoke a tool by name with a dict of arguments |

## How tool loops work

When Claude decides to use a tool:

1. Solarium receives the `tool_use` block from Claude
2. Calls the matching Python function with Claude's arguments
3. Sends the result back to Claude as a `tool_result`
4. Claude continues — possibly calling more tools or returning a final answer

This loop runs up to `agent.max_iterations` times per turn.

## Example: multi-tool agent

```python
import solarium

@solarium.tool
def calculator(expression: str) -> str:
    """Evaluate a math expression."""
    return str(eval(expression))

@solarium.tool
def get_time(timezone: str) -> str:
    """Return the current time in a timezone."""
    from datetime import datetime
    import zoneinfo
    tz = zoneinfo.ZoneInfo(timezone)
    return datetime.now(tz).strftime("%H:%M %Z")

registry = solarium.ToolRegistry()
registry.register_all(calculator, get_time)

agent = solarium.Agent(name="utility-bot", tools=registry)
print(agent.run("What time is it in Tokyo, and what is 15% of 847?"))
```
