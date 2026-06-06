# Solarium

**An AI agent framework dedicated to the Solana blockchain.**

Solarium gives you intelligent, autonomous agents that live on-chain. Each agent controls its own Solana wallet, executes transactions, monitors token balances, and coordinates with other agents — all driven by Claude's adaptive reasoning.

Build DeFi bots, treasury managers, on-chain oracles, multi-agent trading systems, and more.

---

## What is Solarium?

Solarium merges two ideas:

1. **Agentic AI** — Claude-powered agents that can reason, plan, use tools, and hand tasks off to each other.
2. **Solana** — each agent gets a first-class Solana wallet with built-in tools for interacting with the chain.

The result is a framework where your agents don't just *talk about* blockchain actions — they *do* them.

---

## Install

```bash
pip install solarium
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Quickstart

### Solana agent with a wallet

```python
import solarium

wallet = solarium.SolanaWallet.generate()   # devnet by default
print(f"Agent wallet: {wallet.pubkey}")

agent = solarium.Agent(
    name="treasury",
    role="Solana treasury manager",
    system=(
        "You manage a Solana devnet wallet. "
        "Use your tools to check balances, request airdrops, and send SOL."
    ),
    tools=wallet.make_tools(),
)

# Agent calls get_sol_balance tool automatically
print(agent.run("What is my current SOL balance?"))

# Agent calls request_airdrop tool
print(agent.run("Request 2 SOL from the devnet faucet."))

# Agent calls send_sol tool
print(agent.run("Send 0.5 SOL to GsbwXfJraMomNxBcjYLcG3mxkBUiyWXAB32fGbSMQRdW"))
```

### SPL token discovery

```python
import solarium

wallet = solarium.SolanaWallet.from_private_key(your_b64_key, rpc_url=solarium.SolanaWallet.MAINNET)
agent = solarium.Agent(
    name="portfolio",
    role="Solana portfolio tracker",
    tools=wallet.make_tools(),
)

print(agent.run("Show me all my SPL token balances."))
print(agent.run("What is my USDC balance?"))
```

### Multi-agent DeFi network

```python
import solarium
from solarium import Topology

# Each agent gets its own wallet and specialization
analyst_wallet = solarium.SolanaWallet.generate()
trader_wallet = solarium.SolanaWallet.generate()

analyst = solarium.Agent(
    name="analyst",
    role="on-chain analyst",
    system="Analyze on-chain data and recommend actions. Hand off trades to 'trader'.",
    tools=analyst_wallet.make_tools(),
)
trader = solarium.Agent(
    name="trader",
    role="execution agent",
    system="Execute trades on Solana when instructed. Confirm every transaction.",
    tools=trader_wallet.make_tools(),
)

network = solarium.Network(topology=Topology.STAR)
network.add(analyst).add(trader)

orchestrator = solarium.Orchestrator(network, entry="analyst")
print(orchestrator.run("Check the treasury balance and send 0.1 SOL to the cold wallet."))
```

### Shared blackboard for on-chain coordination

```python
import solarium

board = solarium.Blackboard()

wallet_a = solarium.SolanaWallet.generate()
wallet_b = solarium.SolanaWallet.generate()

agent_a = solarium.Agent(name="agent_a", role="monitor", tools=wallet_a.make_tools())
agent_b = solarium.Agent(name="agent_b", role="executor", tools=wallet_b.make_tools())

network = solarium.Network(blackboard=board)
network.add(agent_a).add(agent_b)

# agent_a writes wallet addresses to the shared blackboard
# agent_b reads them and coordinates transfers
```

---

## Wallet tools

Every `SolanaWallet` comes with 8 built-in agent tools:

| Tool | Description |
|------|-------------|
| `get_wallet_address` | Returns this agent's public key |
| `get_sol_balance` | SOL balance for any address |
| `send_sol` | Transfer SOL to any address |
| `request_airdrop` | Request devnet SOL for testing |
| `get_token_accounts` | List all SPL token accounts |
| `get_spl_balance` | SPL token balance for a specific mint |
| `get_transaction` | Look up any transaction by signature |
| `get_account_info` | Inspect any on-chain account |

---

## Networks and topologies

Solarium supports three agent topologies:

- **`STAR`** — one hub agent routes tasks to specialists
- **`PIPELINE`** — agents run in sequence, each passing output to the next
- **`MESH`** — any agent can hand off to any other

---

## Blackboard: shared on-chain state

The `Blackboard` is a thread-safe shared memory store that all agents in a `Network` can read and write. Use it to coordinate on-chain data across agents — broadcast wallet addresses, signal trade conditions, track portfolio state.

```python
board = solarium.Blackboard()
board.write("treasury_address", wallet.pubkey, author="admin")

# All agents in the network get blackboard_read / blackboard_write tools injected
network = solarium.Network(blackboard=board)
network.add(agent_a).add(agent_b)
```

---

## Networks

```
solarium/
├── agent.py          # Agent — Claude + tools + memory + handoffs
├── orchestrator.py   # Orchestrator — drives multi-agent loops
├── network.py        # Network + Topology — wires agents together
├── memory.py         # Memory — rolling history + KV store
├── blackboard.py     # Blackboard — shared agent memory
├── solana_tools.py   # SolanaWallet + 8 on-chain tools
├── tools.py          # @tool decorator + ToolRegistry
└── providers/        # Anthropic + OpenAI-compatible providers
```

---

## Multi-provider support

Solarium uses Anthropic Claude by default. You can swap in any OpenAI-compatible provider (Groq, Together AI, Ollama, etc.):

```python
agent = solarium.Agent(
    name="fast",
    provider=solarium.OpenAIProvider(),
    model="mixtral-8x7b-32768",
    api_key="gsk_...",
)
```

---

## Mainnet vs devnet

```python
# Devnet (default) — free airdrops, safe for testing
wallet = solarium.SolanaWallet.generate()

# Mainnet — real SOL, real consequences
wallet = solarium.SolanaWallet.generate(rpc_url=solarium.SolanaWallet.MAINNET)

# Custom RPC (Helius, Alchemy, QuickNode, etc.)
wallet = solarium.SolanaWallet.generate(rpc_url="https://rpc.helius.xyz/?api-key=...")
```

---

## Development

```bash
git clone https://github.com/jaenanjs/Solarium
cd Solarium
pip install -e ".[dev]"
pytest
ruff check solarium tests
mypy solarium
```

---

## License

MIT — see [LICENSE](LICENSE).
