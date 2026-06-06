"""Example 6 — Solana agent: an AI treasurer that manages a devnet wallet.

The agent can check balances, request airdrops, send SOL, and look up
transactions — all autonomously using its on-chain tools.

Requires: pip install solarium[solana]
"""

import solarium
from solarium.solana_tools import SolanaWallet

# Generate a fresh devnet wallet for this agent
wallet = SolanaWallet.generate(rpc_url=SolanaWallet.DEVNET)
print(f"Agent wallet: {wallet.pubkey}\n")

agent = solarium.Agent(
    name="treasurer",
    role="Solana treasury manager",
    system=(
        "You are a Solana treasury agent. You manage a devnet wallet. "
        "When asked to perform on-chain actions, use your tools to do so and "
        "report the results clearly. Always confirm transaction signatures."
    ),
    tools=wallet.make_tools(),
)

if __name__ == "__main__":
    # 1. Check initial balance
    print(agent.run("What is my current SOL balance?"))
    print()

    # 2. Request an airdrop
    print(agent.run("Request an airdrop of 1 SOL so I can test with it."))
    print()

    # 3. Check balance again
    print(agent.run("Check my balance again and confirm the airdrop landed."))
