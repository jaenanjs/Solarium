"""Example 5 — Blackboard: agents collaborating through shared memory.

Three agents work together on a research task:
  1. researcher  — gathers information, writes findings to the blackboard
  2. analyst     — reads the researcher's findings, writes an analysis
  3. writer      — reads both and produces a final report

No explicit handoffs. They coordinate purely through shared state.
"""

import asyncio
import solarium
from solarium.network import Topology

board = solarium.Blackboard()

# Watch the blackboard — print every write in real time
board.watch("findings", lambda e: print(f"\n[blackboard] {e.author} wrote 'findings'"))
board.watch("analysis", lambda e: print(f"[blackboard] {e.author} wrote 'analysis'"))

network = solarium.Network(topology=Topology.PIPELINE, blackboard=board)

researcher = solarium.Agent(
    name="researcher",
    system=(
        "You are a research specialist. Given a topic, write 3 key facts about it. "
        "Use blackboard_write to store your findings under the key 'findings'. "
        "Then summarize what you wrote in one sentence."
    ),
)

analyst = solarium.Agent(
    name="analyst",
    system=(
        "You are a data analyst. Use blackboard_read to read the 'findings' key. "
        "Identify the most important insight and write it to the blackboard under 'analysis'. "
        "Then briefly state your conclusion."
    ),
)

writer = solarium.Agent(
    name="writer",
    system=(
        "You are a professional writer. Use blackboard_read to read both 'findings' and 'analysis'. "
        "Combine them into a polished 2-sentence summary suitable for a general audience."
    ),
)

network.add(researcher).add(analyst).add(writer)
orchestrator = solarium.Orchestrator(network)


async def main() -> None:
    transcript = await orchestrator.arun_pipeline("the James Webb Space Telescope")
    print("\n" + "=" * 50)
    for agent_name, output in transcript:
        print(f"\n[{agent_name}]\n{output}")
    print("\n" + "=" * 50)
    print("\nFinal blackboard state:")
    for key, value in board.snapshot().items():
        print(f"  {key}: {value[:80]}...")


if __name__ == "__main__":
    asyncio.run(main())
