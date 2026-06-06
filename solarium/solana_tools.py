"""Solana integration — wallets and on-chain tools for Solarium agents.

Core capabilities:
  - SOL balance checks and transfers
  - SPL token balance checks and transfers
  - Associated token account discovery
  - Transaction lookup and status
  - Devnet airdrops for testing
  - Arbitrary account data inspection

Usage::

    from solarium import SolanaWallet

    wallet = SolanaWallet.generate()            # fresh keypair on devnet
    wallet = SolanaWallet.from_private_key(b64) # load existing key
    wallet = SolanaWallet(keypair, rpc_url)     # BYO keypair

    agent = solarium.Agent(
        name="trader",
        role="Solana DeFi agent",
        tools=wallet.make_tools(),
    )
"""

from __future__ import annotations

import base64
import json
from typing import Any

from solarium.tools import ToolRegistry, tool

_LAMPORTS_PER_SOL = 1_000_000_000
_TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
_ASSOCIATED_TOKEN_PROGRAM_ID = "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJe1bj8"


class SolanaWallet:
    """A Solana keypair with pre-built agent tools for on-chain interactions.

    Args:
        keypair: A ``solders.keypair.Keypair`` instance.
        rpc_url: Solana RPC endpoint. Defaults to devnet.
    """

    DEVNET = "https://api.devnet.solana.com"
    MAINNET = "https://api.mainnet-beta.solana.com"
    TESTNET = "https://api.testnet.solana.com"

    def __init__(self, keypair: Any, rpc_url: str = DEVNET) -> None:
        self._keypair = keypair
        self._rpc_url = rpc_url

        from solana.rpc.api import Client
        self._client = Client(rpc_url)

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def generate(cls, rpc_url: str = DEVNET) -> SolanaWallet:
        """Create a brand-new random keypair."""
        from solders.keypair import Keypair
        return cls(Keypair(), rpc_url)

    @classmethod
    def from_private_key(cls, private_key_b64: str, rpc_url: str = DEVNET) -> SolanaWallet:
        """Load a wallet from a base64-encoded 64-byte private key."""
        from solders.keypair import Keypair
        raw = base64.b64decode(private_key_b64)
        return cls(Keypair.from_bytes(raw), rpc_url)

    @classmethod
    def from_secret_key_bytes(cls, secret: bytes, rpc_url: str = DEVNET) -> SolanaWallet:
        """Load a wallet from raw secret key bytes."""
        from solders.keypair import Keypair
        return cls(Keypair.from_bytes(secret), rpc_url)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def pubkey(self) -> str:
        return str(self._keypair.pubkey())

    @property
    def private_key_b64(self) -> str:
        """Base64-encoded 64-byte secret key. Keep this secret."""
        return base64.b64encode(bytes(self._keypair)).decode()

    @property
    def rpc_url(self) -> str:
        return self._rpc_url

    # ------------------------------------------------------------------
    # SOL operations
    # ------------------------------------------------------------------

    def _get_balance_lamports(self, address: str | None = None) -> int:
        from solders.pubkey import Pubkey
        pubkey = Pubkey.from_string(address) if address else self._keypair.pubkey()
        resp = self._client.get_balance(pubkey)
        return resp.value

    def _send_sol(self, recipient: str, amount_sol: float) -> str:
        from solders.message import Message
        from solders.pubkey import Pubkey
        from solders.system_program import TransferParams, transfer
        from solders.transaction import Transaction

        lamports = int(amount_sol * _LAMPORTS_PER_SOL)
        to_pubkey = Pubkey.from_string(recipient)

        blockhash_resp = self._client.get_latest_blockhash()
        blockhash = blockhash_resp.value.blockhash

        ix = transfer(TransferParams(
            from_pubkey=self._keypair.pubkey(),
            to_pubkey=to_pubkey,
            lamports=lamports,
        ))
        msg = Message.new_with_blockhash([ix], self._keypair.pubkey(), blockhash)
        txn = Transaction([self._keypair], msg, blockhash)

        result = self._client.send_raw_transaction(bytes(txn))
        return str(result.value)

    def _request_airdrop(self, amount_sol: float) -> str:
        lamports = int(amount_sol * _LAMPORTS_PER_SOL)
        result = self._client.request_airdrop(self._keypair.pubkey(), lamports)
        return str(result.value)

    # ------------------------------------------------------------------
    # SPL token operations
    # ------------------------------------------------------------------

    def _get_token_accounts(self, owner: str | None = None) -> list[dict[str, Any]]:
        """Return all SPL token accounts owned by an address."""
        from solders.pubkey import Pubkey
        owner_pubkey = Pubkey.from_string(owner) if owner else self._keypair.pubkey()

        resp = self._client.get_token_accounts_by_owner_json_parsed(
            owner_pubkey,
            {"programId": _TOKEN_PROGRAM_ID},  # type: ignore[arg-type]
        )
        accounts = []
        for item in resp.value:
            raw_parsed = item.account.data.parsed
            parsed: dict[str, Any] = raw_parsed
            info: dict[str, Any] = parsed["info"]
            token_amount: dict[str, Any] = info["tokenAmount"]
            accounts.append({
                "address": str(item.pubkey),
                "mint": info["mint"],
                "owner": info["owner"],
                "amount": token_amount["uiAmountString"],
                "decimals": token_amount["decimals"],
            })
        return accounts

    def _get_spl_balance(self, mint: str, owner: str | None = None) -> dict[str, Any]:
        """Return SPL token balance for a specific mint."""
        accounts = self._get_token_accounts(owner)
        for acc in accounts:
            if acc["mint"] == mint:
                return acc
        owner_addr = owner or self.pubkey
        return {"mint": mint, "owner": owner_addr, "amount": "0", "decimals": 0}

    # ------------------------------------------------------------------
    # Transaction and account lookup
    # ------------------------------------------------------------------

    def _get_transaction(self, signature: str) -> dict[str, Any]:
        from solders.signature import Signature
        sig = Signature.from_string(signature)
        resp = self._client.get_transaction(sig, max_supported_transaction_version=0)
        if resp.value is None:
            return {"error": "Transaction not found"}
        meta = resp.value.transaction.meta
        return {
            "signature": signature,
            "slot": resp.value.slot,
            "fee": meta.fee if meta else None,
            "err": str(meta.err) if meta and meta.err else None,
            "status": "success" if (meta and meta.err is None) else "failed",
        }

    def _get_account_info(self, address: str) -> dict[str, Any]:
        from solders.pubkey import Pubkey
        pubkey = Pubkey.from_string(address)
        resp = self._client.get_account_info(pubkey)
        if resp.value is None:
            return {"error": f"Account {address} not found"}
        acc = resp.value
        return {
            "address": address,
            "lamports": acc.lamports,
            "sol": acc.lamports / _LAMPORTS_PER_SOL,
            "owner": str(acc.owner),
            "executable": acc.executable,
            "rent_epoch": acc.rent_epoch,
        }

    # ------------------------------------------------------------------
    # Tool registry factory
    # ------------------------------------------------------------------

    def make_tools(self) -> ToolRegistry:
        """Return a ToolRegistry with all Solana tools bound to this wallet."""
        wallet = self

        @tool(description="Get SOL balance of a wallet. Omit address for agent wallet.")
        def get_sol_balance(address: str = "") -> str:
            lamports = wallet._get_balance_lamports(address or None)
            sol = lamports / _LAMPORTS_PER_SOL
            target = address or wallet.pubkey
            return f"{sol:.9f} SOL ({lamports} lamports) at {target}"

        @tool(description="Send SOL to a recipient wallet address.")
        def send_sol(recipient: str, amount_sol: float) -> str:
            sig = wallet._send_sol(recipient, amount_sol)
            return f"Sent {amount_sol} SOL to {recipient}. Signature: {sig}"

        @tool(description="Look up a Solana transaction by its signature.")
        def get_transaction(signature: str) -> str:
            result = wallet._get_transaction(signature)
            return json.dumps(result, indent=2)

        @tool(description="Get info about any Solana account or wallet address.")
        def get_account_info(address: str) -> str:
            result = wallet._get_account_info(address)
            return json.dumps(result, indent=2)

        @tool(description="Get this agent's own Solana wallet address (public key).")
        def get_wallet_address() -> str:
            return f"This agent's wallet address: {wallet.pubkey}"

        @tool(description="Request a devnet SOL airdrop for testing. Devnet only.")
        def request_airdrop(amount_sol: float) -> str:
            sig = wallet._request_airdrop(amount_sol)
            return f"Airdrop of {amount_sol} SOL requested. Signature: {sig}"

        @tool(description="List all SPL token accounts held by a wallet address.")
        def get_token_accounts(address: str = "") -> str:
            accounts = wallet._get_token_accounts(address or None)
            if not accounts:
                return "No SPL token accounts found."
            return json.dumps(accounts, indent=2)

        @tool(description="Get SPL token balance for a specific mint address.")
        def get_spl_balance(mint: str, address: str = "") -> str:
            result = wallet._get_spl_balance(mint, address or None)
            return json.dumps(result, indent=2)

        registry = ToolRegistry()
        registry.register_all(
            get_sol_balance,
            send_sol,
            get_transaction,
            get_account_info,
            get_wallet_address,
            request_airdrop,
            get_token_accounts,
            get_spl_balance,
        )
        return registry

    def __repr__(self) -> str:
        if "mainnet" in self._rpc_url:
            network = "mainnet"
        elif "devnet" in self._rpc_url:
            network = "devnet"
        else:
            network = "custom"
        return f"SolanaWallet(pubkey={self.pubkey}, network={network})"
