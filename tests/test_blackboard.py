"""Tests for Blackboard."""

from solarium.blackboard import Blackboard


def test_write_and_read():
    board = Blackboard()
    board.write("key", "value", author="agent-a")
    assert board.read("key") == "value"


def test_read_missing_returns_default():
    board = Blackboard()
    assert board.read("missing") is None
    assert board.read("missing", default="fallback") == "fallback"


def test_history_tracks_all_writes():
    board = Blackboard()
    board.write("x", "first", author="a")
    board.write("x", "second", author="b")
    entries = board.history("x")
    assert len(entries) == 2
    assert entries[0].value == "first"
    assert entries[0].author == "a"
    assert entries[1].value == "second"
    assert entries[1].author == "b"


def test_last_author():
    board = Blackboard()
    board.write("k", "v1", author="alice")
    board.write("k", "v2", author="bob")
    assert board.last_author("k") == "bob"
    assert board.last_author("nonexistent") is None


def test_snapshot():
    board = Blackboard()
    board.write("a", 1)
    board.write("b", 2)
    snap = board.snapshot()
    assert snap == {"a": 1, "b": 2}


def test_delete():
    board = Blackboard()
    board.write("k", "v")
    board.delete("k")
    assert board.read("k") is None


def test_keys():
    board = Blackboard()
    board.write("x", 1)
    board.write("y", 2)
    assert set(board.keys()) == {"x", "y"}


def test_watch_fires_on_write():
    board = Blackboard()
    calls = []
    board.watch("k", lambda e: calls.append(e.value))
    board.write("k", "hello", author="bot")
    board.write("k", "world", author="bot")
    assert calls == ["hello", "world"]


def test_watch_only_fires_for_its_key():
    board = Blackboard()
    calls = []
    board.watch("target", lambda e: calls.append(e))
    board.write("other", "irrelevant")
    assert calls == []


def test_unwatch():
    board = Blackboard()
    calls = []
    def cb(e):
        return calls.append(e)
    board.watch("k", cb)
    board.unwatch("k", cb)
    board.write("k", "v")
    assert calls == []


def test_full_history_ordered():
    board = Blackboard()
    board.write("a", 1, author="x")
    board.write("b", 2, author="y")
    board.write("a", 3, author="z")
    hist = board.full_history()
    assert len(hist) == 3
    assert {e.value for e in hist} == {1, 2, 3}


def test_make_tools_read_write():
    board = Blackboard()
    board.write("fact", "the sky is blue", author="setup")
    specs = board.make_tools("test-agent")
    assert len(specs) == 2
    names = {s["name"] for s in specs}
    assert names == {"blackboard_read", "blackboard_write"}

    read_handler = next(s["_handler"] for s in specs if s["name"] == "blackboard_read")
    write_handler = next(s["_handler"] for s in specs if s["name"] == "blackboard_write")

    assert "sky is blue" in read_handler(key="fact")
    write_handler(key="new_key", value="new_value")
    assert board.read("new_key") == "new_value"
    assert board.last_author("new_key") == "test-agent"
