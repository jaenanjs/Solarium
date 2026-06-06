"""Example 3 — pipeline topology: each agent refines the previous output."""

import axon
from axon.network import Topology

network = axon.Network(topology=Topology.PIPELINE)

drafter = axon.Agent(
    name="drafter",
    role="first-draft writer",
    system="You write concise first drafts. Given a topic, produce a 3-sentence paragraph.",
)

editor = axon.Agent(
    name="editor",
    role="copy editor",
    system=(
        "You are a copy editor. Improve the draft you receive: fix grammar, "
        "tighten sentences, and improve clarity. Return only the edited text."
    ),
)

critic = axon.Agent(
    name="critic",
    role="quality reviewer",
    system=(
        "You are a quality reviewer. Score the text you receive on clarity (1-10) "
        "and conciseness (1-10) and explain your scores in one sentence each."
    ),
)

network.add(drafter).add(editor).add(critic)
orchestrator = axon.Orchestrator(network)

if __name__ == "__main__":
    import asyncio

    async def main() -> None:
        transcript = await orchestrator.arun_pipeline("the James Webb Space Telescope")
        for agent_name, output in transcript:
            print(f"\n=== {agent_name} ===")
            print(output)

    asyncio.run(main())
