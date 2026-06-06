"""Tests for Memory."""

from axon.memory import Memory
from axon.message import Message


def test_add_and_retrieve():
    mem = Memory()
    mem.add(Message.user("hello"))
    mem.add(Message.assistant("hi there"))
    assert len(mem.messages()) == 2


def test_api_messages_format():
    mem = Memory()
    mem.add(Message.user("ping"))
    mem.add(Message.assistant("pong"))
    api = mem.api_messages()
    assert api == [{"role": "user", "content": "ping"}, {"role": "assistant", "content": "pong"}]


def test_max_messages_rolling():
    mem = Memory(max_messages=3)
    for i in range(5):
        mem.add(Message.user(str(i)))
    msgs = mem.messages()
    assert len(msgs) == 3
    assert msgs[-1].content == "4"


def test_kv_store():
    mem = Memory()
    mem.remember("key", {"a": 1})
    assert mem.recall("key") == {"a": 1}
    mem.forget("key")
    assert mem.recall("key") is None


def test_clear_history():
    mem = Memory()
    mem.add(Message.user("x"))
    mem.clear_history()
    assert mem.messages() == []
