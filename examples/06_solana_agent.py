"""Example 6 — Solana agent: an AI treasury manager on devnet.

The agent controls its own Solana wallet and can autonomously:
  - Check SOL and SPL token balances
  - Request devnet airdrops
  - Send SOL transactions
  - Look up transaction history

Run:
    export ANTHROPIC_API_KEY=sk-ant-...
    python examples/06_solana_agent.py
"""

import solarium

# Every agent gets its own Solana wallet
wallet = solarium.SolanaWallet.generate(rpc_url=solarium.SolanaWallet.DEVNET)
print(f"Agent wallet: {wallet.pubkey}\n")

agent = solarium.Agent(
    name="treasury",
    role="Solana treasury manager",
    system=(
        "You are a Solana treasury agent operating on devnet. "
        "You manage a wallet and can perform on-chain actions using your tools. "
        "Always confirm transaction signatures and report results clearly."
    ),
    tools=wallet.make_tools(),
)

if __name__ == "__main__":
    # Check the starting balance
    print("=== Balance check ===")
    print(agent.run("What is my current SOL balance?"))
    print()

    # Fund the wallet via airdrop
    print("=== Airdrop ===")
    print(agent.run("Request an airdrop of 2 SOL so I can run tests."))
    print()

    # Confirm the airdrop landed
    print("=== Confirm ===")
    print(agent.run("Check my balance again and confirm the airdrop arrived."))
    print()

    # List any SPL tokens
    print("=== Token accounts ===")
    print(agent.run("Do I hold any SPL tokens?"))
