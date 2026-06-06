"""Tests for ToolRegistry and @tool decorator."""

import pytest

from solarium.tools import ToolRegistry, tool


@tool
def add(x: int, y: int) -> int:
    """Add two integers."""
    return x + y


@tool(name="greet", description="Return a greeting.")
def greet_fn(name: str) -> str:
    return f"Hello, {name}!"


def test_tool_spec_generated():
    spec = add._solarium_tool_spec
    assert spec["name"] == "add"
    assert spec["description"] == "Add two integers."
    assert "x" in spec["input_schema"]["properties"]
    assert "y" in spec["input_schema"]["properties"]
    assert spec["input_schema"]["required"] == ["x", "y"]


def test_tool_custom_name():
    assert greet_fn._solarium_tool_spec["name"] == "greet"
    assert greet_fn._solarium_tool_spec["description"] == "Return a greeting."


def test_registry_register_and_call():
    reg = ToolRegistry()
    reg.register(add)
    assert "add" in reg
    assert reg.call("add", {"x": 3, "y": 4}) == 7


def test_registry_unknown_tool_raises():
    reg = ToolRegistry()
    with pytest.raises(KeyError):
        reg.call("nonexistent", {})


def test_registry_specs():
    reg = ToolRegistry()
    reg.register_all(add, greet_fn)
    assert len(reg.specs()) == 2


def test_undecorated_fn_raises():
    def bare(): pass
    reg = ToolRegistry()
    with pytest.raises(ValueError):
        reg.register(bare)
