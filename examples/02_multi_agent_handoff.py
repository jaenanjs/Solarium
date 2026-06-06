"""Example 2 — star topology: a router hands off to specialists."""

import axon
from axon.network import Topology


@axon.tool
def web_search(query: str) -> str:
    """Simulate a web search (stub — replace with real search API)."""
    return f"[Search results for '{query}'] Top result: Wikipedia article on {query.split()[0]}."


@axon.tool
def run_python(code: str) -> str:
    """Execute Python code safely (stub — replace with sandbox)."""
    try:
        local_vars: dict = {}
        exec(code, {"__builtins__": {"print": print, "range": range, "len": len}}, local_vars)  # noqa: S102
        return str(local_vars)
    except Exception as e:
        return f"Error: {e}"


search_tools = axon.ToolRegistry()
search_tools.register(web_search)

code_tools = axon.ToolRegistry()
code_tools.register(run_python)

network = axon.Network(topology=Topology.STAR)

router = axon.Agent(
    name="router",
    role="task router that delegates to the right specialist",
    system=(
        "You are a routing agent. Analyze the user's request and hand off to "
        "'researcher' for information lookup tasks or 'coder' for programming tasks. "
        "Use the _axon_handoff tool to delegate. Never answer directly."
    ),
)

researcher = axon.Agent(
    name="researcher",
    role="research specialist with web search capability",
    tools=search_tools,
)

coder = axon.Agent(
    name="coder",
    role="Python coding specialist",
    tools=code_tools,
)

network.add(router).add(researcher).add(coder)
orchestrator = axon.Orchestrator(network, entry="router")

if __name__ == "__main__":
    result = orchestrator.run("Write a Python function that computes Fibonacci numbers.")
    print(result)
