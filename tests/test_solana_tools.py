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
    assert len(registry) == 6
    expected = {
        "get_sol_balance", "send_sol", "get_transaction",
        "get_account_info", "get_wallet_address", "request_airdrop",
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
