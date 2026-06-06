"""Tests for SolanaWallet — unit tests only, no network calls."""

import base64
from unittest.mock import MagicMock

from solarium.solana_tools import _LAMPORTS_PER_SOL, SolanaWallet


def test_generate_creates_unique_wallets():
    w1 = SolanaWallet.generate()
    w2 = SolanaWallet.generate()
    assert w1.pubkey != w2.pubkey


def test_pubkey_is_string():
    wallet = SolanaWallet.generate()
    assert isinstance(wallet.pubkey, str)
    assert len(wallet.pubkey) > 30


def test_private_key_roundtrip():
    wallet = SolanaWallet.generate()
    b64 = wallet.private_key_b64
    restored = SolanaWallet.from_private_key(b64)
    assert restored.pubkey == wallet.pubkey


def test_from_secret_key_bytes():
    wallet = SolanaWallet.generate()
    raw = base64.b64decode(wallet.private_key_b64)
    restored = SolanaWallet.from_secret_key_bytes(raw)
    assert restored.pubkey == wallet.pubkey


def test_repr_shows_network():
    wallet = SolanaWallet.generate(rpc_url=SolanaWallet.DEVNET)
    assert "devnet" in repr(wallet)

    wallet_main = SolanaWallet.generate(rpc_url=SolanaWallet.MAINNET)
    assert "mainnet" in repr(wallet_main)


def test_make_tools_returns_registry():
    wallet = SolanaWallet.generate()
    registry = wallet.make_tools()
    assert len(registry) == 11
    expected = {
        "get_sol_balance", "send_sol", "send_spl_token", "get_transaction",
        "get_account_info", "get_wallet_address", "request_airdrop",
        "get_token_accounts", "get_spl_balance", "get_swap_quote", "execute_swap",
    }
    assert {s["name"] for s in registry.specs()} == expected


def test_get_wallet_address_tool():
    wallet = SolanaWallet.generate()
    registry = wallet.make_tools()
    result = registry.call("get_wallet_address", {})
    assert wallet.pubkey in result


def test_get_sol_balance_calls_rpc():
    wallet = SolanaWallet.generate()
    wallet._get_balance_lamports = MagicMock(return_value=int(2.5 * _LAMPORTS_PER_SOL))
    registry = wallet.make_tools()
    result = registry.call("get_sol_balance", {"address": ""})
    assert "2.5" in result
    assert "SOL" in result


def test_send_sol_calls_rpc():
    wallet = SolanaWallet.generate()
    fake_sig = "5xFakeSignature123"
    wallet._send_sol = MagicMock(return_value=fake_sig)
    registry = wallet.make_tools()
    system_program = "So11111111111111111111111111111111111111112"
    result = registry.call("send_sol", {"recipient": system_program, "amount_sol": 0.1})
    assert fake_sig in result
    assert "0.1" in result


def test_request_airdrop_calls_rpc():
    wallet = SolanaWallet.generate()
    wallet._request_airdrop = MagicMock(return_value="AirdropSig123")
    registry = wallet.make_tools()
    result = registry.call("request_airdrop", {"amount_sol": 1.0})
    assert "AirdropSig123" in result


def test_get_token_accounts_tool():
    wallet = SolanaWallet.generate()
    wallet._get_token_accounts = MagicMock(return_value=[
        {"address": "TokenAccAddr", "mint": "MintAddr", "owner": wallet.pubkey,
         "amount": "100.0", "decimals": 6},
    ])
    registry = wallet.make_tools()
    result = registry.call("get_token_accounts", {"address": ""})
    import json
    parsed = json.loads(result)
    assert parsed[0]["mint"] == "MintAddr"
    assert parsed[0]["amount"] == "100.0"


def test_get_spl_balance_tool():
    wallet = SolanaWallet.generate()
    wallet._get_spl_balance = MagicMock(return_value={
        "mint": "USDCMint", "owner": wallet.pubkey, "amount": "50.0", "decimals": 6,
    })
    registry = wallet.make_tools()
    result = registry.call("get_spl_balance", {"mint": "USDCMint", "address": ""})
    import json
    parsed = json.loads(result)
    assert parsed["amount"] == "50.0"
    assert parsed["mint"] == "USDCMint"


def test_send_spl_token_tool():
    wallet = SolanaWallet.generate()
    wallet._send_spl_token = MagicMock(return_value="SplTransferSig456")
    registry = wallet.make_tools()
    system_program = "So11111111111111111111111111111111111111112"
    result = registry.call("send_spl_token", {
        "mint": "USDCMintAddress",
        "recipient": system_program,
        "amount": 10.0,
    })
    assert "SplTransferSig456" in result
    assert "10.0" in result


def test_get_swap_quote_tool():
    wallet = SolanaWallet.generate()
    usdc = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    sol = "So11111111111111111111111111111111111111112"
    wallet._jupiter_quote = MagicMock(
        return_value={"outAmount": "1500000000", "priceImpactPct": "0.01"}
    )
    wallet._get_token_decimals = MagicMock(return_value=9)
    registry = wallet.make_tools()
    result = registry.call("get_swap_quote", {
        "input_mint": usdc, "output_mint": sol, "amount": 100.0, "slippage_bps": 50,
    })
    assert "1.5" in result
    assert "0.01" in result


def test_execute_swap_tool():
    wallet = SolanaWallet.generate()
    usdc = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    sol = "So11111111111111111111111111111111111111112"
    wallet._jupiter_swap = MagicMock(return_value="SwapSig789")
    registry = wallet.make_tools()
    result = registry.call("execute_swap", {
        "input_mint": usdc, "output_mint": sol, "amount": 50.0, "slippage_bps": 50,
    })
    assert "SwapSig789" in result


def test_get_transaction_tool_formats_json():
    wallet = SolanaWallet.generate()
    wallet._get_transaction = MagicMock(return_value={
        "signature": "abc123",
        "slot": 100,
        "fee": 5000,
        "err": None,
        "status": "success",
    })
    registry = wallet.make_tools()
    result = registry.call("get_transaction", {"signature": "abc123"})
    import json
    parsed = json.loads(result)
    assert parsed["status"] == "success"
    assert parsed["signature"] == "abc123"
