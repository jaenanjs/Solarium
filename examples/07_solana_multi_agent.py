"""Example 7 — Multi-agent Solana network with shared blackboard.

Two agents cooperate on-chain:
  - monitor: watches balances and writes signals to the blackboard
  - executor: reads signals and executes transfers

Run:
    export ANTHROPIC_API_KEY=sk-ant-...
    python examples/07_solana_multi_agent.py
"""

import solarium
from solarium import Topology

# Each agent controls its own Solana wallet
monitor_wallet = solarium.SolanaWallet.generate(rpc_url=solarium.SolanaWallet.DEVNET)
executor_wallet = solarium.SolanaWallet.generate(rpc_url=solarium.SolanaWallet.DEVNET)

print(f"Monitor wallet:  {monitor_wallet.pubkey}")
print(f"Executor wallet: {executor_wallet.pubkey}\n")

# Shared blackboard for on-chain coordination
board = solarium.Blackboard()
board.write("executor_address", executor_wallet.pubkey, author="system",
            note="executor agent's receiving address")

monitor = solarium.Agent(
    name="monitor",
    role="on-chain monitor",
    system=(
        "You monitor Solana wallets and report on-chain state. "
        "Write important findings to the blackboard using blackboard_write. "
        "Hand off to 'executor' when a transfer needs to happen."
    ),
    tools=monitor_wallet.make_tools(),
)

executor = solarium.Agent(
    name="executor",
    role="transaction executor",
    system=(
        "You execute Solana transactions. "
        "Read instructions from the blackboard with blackboard_read before acting. "
        "Confirm every transaction signature."
    ),
    tools=executor_wallet.make_tools(),
)

network = solarium.Network(topology=Topology.STAR, blackboard=board)
network.add(monitor).add(executor)

orchestrator = solarium.Orchestrator(network, entry="monitor")

if __name__ == "__main__":
    result = orchestrator.run(
        "Check the monitor wallet's SOL balance, write it to the blackboard, "
        "then ask the executor to check its own balance too."
    )
    print(result)
