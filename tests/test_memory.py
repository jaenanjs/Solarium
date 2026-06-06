"""Tests for Memory."""

from solarium.memory import Memory


def test_add_and_retrieve():
    mem = Memory()
    mem.add_internal({"role": "user", "content": "hello"})
    mem.add_internal({"role": "assistant", "content": "hi there"})
    assert len(mem.internal_messages()) == 2


def test_internal_messages_format():
    mem = Memory()
    mem.add_internal({"role": "user", "content": "ping"})
    mem.add_internal({"role": "assistant", "content": "pong"})
    msgs = mem.internal_messages()
    assert msgs[0] == {"role": "user", "content": "ping"}
    assert msgs[1] == {"role": "assistant", "content": "pong"}


def test_max_messages_rolling():
    mem = Memory(max_messages=3)
    for i in range(5):
        mem.add_internal({"role": "user", "content": str(i)})
    msgs = mem.internal_messages()
    assert len(msgs) == 3
    assert msgs[-1]["content"] == "4"


def test_kv_store():
    mem = Memory()
    mem.remember("key", {"a": 1})
    assert mem.recall("key") == {"a": 1}
    mem.forget("key")
    assert mem.recall("key") is None


def test_clear_history():
    mem = Memory()
    mem.add_internal({"role": "user", "content": "x"})
    mem.clear_history()
    assert mem.internal_messages() == []
