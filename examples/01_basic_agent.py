"""Example 1 — single agent with a custom tool."""

import solarium


@solarium.tool
def calculator(expression: str) -> str:
    """Evaluate a safe arithmetic expression and return the result."""
    try:
        result = eval(expression, {"__builtins__": {}})  # noqa: S307
        return str(result)
    except Exception as e:
        return f"Error: {e}"


registry = solarium.ToolRegistry()
registry.register(calculator)

agent = solarium.Agent(
    name="math-agent",
    role="precise arithmetic assistant",
    tools=registry,
)

if __name__ == "__main__":
    answer = agent.run("What is 17 * 23 + sqrt(144)? Show your reasoning.")
    print(answer)
