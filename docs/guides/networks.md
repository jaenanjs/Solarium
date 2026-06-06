# Multi-agent networks

Solarium lets you connect multiple agents into a network where they can delegate tasks to each other. This guide covers all three topologies.

## Star topology — routing to specialists

The most common pattern: one agent routes incoming requests to domain specialists.

```python
import solarium
from solarium.network import Topology

# Define specialist tools
@solarium.tool
def search_docs(query: str) -> str:
    """Search the documentation."""
    return f"Documentation results for: {query}"

@solarium.tool
def run_query(sql: str) -> str:
    """Run a SQL query against the database."""
    return f"Query results for: {sql}"

doc_tools = solarium.ToolRegistry()
doc_tools.register(search_docs)

db_tools = solarium.ToolRegistry()
db_tools.register(run_query)

# Build the network
network = solarium.Network(topology=Topology.STAR)

router = solarium.Agent(
    name="router",
    system=(
        "You are a routing agent. For documentation questions, hand off to 'doc-agent'. "
        "For database questions, hand off to 'db-agent'. "
        "Always use _solarium_handoff — never answer directly."
    ),
)

doc_agent = solarium.Agent(
    name="doc-agent",
    role="documentation specialist",
    tools=doc_tools,
)

db_agent = solarium.Agent(
    name="db-agent",
    role="database specialist",
    tools=db_tools,
)

network.add(router).add(doc_agent).add(db_agent)

orchestrator = solarium.Orchestrator(network, entry="router")
print(orchestrator.run("How do I filter a dataframe by date range?"))
```

## Pipeline topology — sequential refinement

Each agent processes the output of the previous one. Great for writing pipelines, data transformation, review workflows.

```python
import asyncio
import solarium
from solarium.network import Topology

network = solarium.Network(topology=Topology.PIPELINE)

network.add(solarium.Agent(
    name="researcher",
    role="research analyst",
    system="Research the given topic and produce a structured outline with key facts.",
))

network.add(solarium.Agent(
    name="writer",
    role="technical writer",
    system="Turn the research outline you receive into a well-written 2-paragraph summary.",
))

network.add(solarium.Agent(
    name="editor",
    role="copy editor",
    system="Edit the text you receive for clarity and conciseness. Return only the final text.",
))

orchestrator = solarium.Orchestrator(network)

async def main():
    transcript = await orchestrator.arun_pipeline("the history of the internet")
    for name, output in transcript:
        print(f"\n{'='*40}\n{name.upper()}\n{'='*40}\n{output}")

asyncio.run(main())
```

## Mesh topology — peer-to-peer

Every agent can hand off to any other. Best for complex workflows where the path isn't predetermined.

```python
import solarium
from solarium.network import Topology

network = solarium.Network(topology=Topology.MESH)

planner = solarium.Agent(
    name="planner",
    system="Break down complex tasks into steps. Hand off subtasks to 'executor' or 'reviewer'.",
)
executor = solarium.Agent(
    name="executor",
    role="task executor",
    system="Execute the task you receive. Hand off to 'reviewer' when done.",
)
reviewer = solarium.Agent(
    name="reviewer",
    role="quality reviewer",
    system="Review the work. Hand back to 'planner' if revisions needed, or return a final answer.",
)

network.add(planner).add(executor).add(reviewer)

orchestrator = solarium.Orchestrator(network, entry="planner", max_handoffs=10)
print(orchestrator.run("Build a content calendar for a tech startup."))
```

## Tips

- **Router system prompts matter** — be explicit about which agent handles what and that it must use `_solarium_handoff`
- **Keep specialists focused** — narrow roles produce better results than general-purpose agents
- **Set `max_handoffs`** — prevents runaway loops in mesh topologies
