"""Example 4 — streaming tokens from a single agent."""

import asyncio
import solarium


agent = solarium.Agent(
    name="storyteller",
    role="creative short-story writer",
)


async def main() -> None:
    print("Streaming response:\n")
    async for token in agent.astream("Write a two-paragraph story about a robot discovering music."):
        print(token, end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(main())
