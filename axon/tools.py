"""Tool registry and decorator for defining agent tools."""

from __future__ import annotations

import inspect
import json
from typing import Any, Callable, get_type_hints


def _python_type_to_json(annotation: Any) -> dict:
    """Map Python type hints to JSON Schema types."""
    if annotation is inspect.Parameter.empty or annotation is type(None):
        return {"type": "string"}
    name = getattr(annotation, "__name__", str(annotation))
    mapping = {
        "str": {"type": "string"},
        "int": {"type": "integer"},
        "float": {"type": "number"},
        "bool": {"type": "boolean"},
        "list": {"type": "array"},
        "dict": {"type": "object"},
    }
    return mapping.get(name, {"type": "string"})


def tool(func: Callable | None = None, *, name: str | None = None, description: str | None = None):
    """Decorator that marks a function as an Axon tool.

    Usage:
        @tool
        def my_tool(x: str) -> str: ...

        @tool(name="custom_name", description="Does X")
        def my_tool(x: str) -> str: ...
    """
    def decorator(fn: Callable) -> Callable:
        tool_name = name or fn.__name__
        tool_desc = description or (fn.__doc__ or "").strip()

        hints = get_type_hints(fn)
        sig = inspect.signature(fn)
        properties: dict[str, Any] = {}
        required: list[str] = []

        for param_name, param in sig.parameters.items():
            annotation = hints.get(param_name, inspect.Parameter.empty)
            properties[param_name] = _python_type_to_json(annotation)
            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        fn._axon_tool = True
        fn._axon_tool_spec = {
            "name": tool_name,
            "description": tool_desc,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }
        return fn

    if func is not None:
        return decorator(func)
    return decorator


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Callable] = {}

    def register(self, fn: Callable) -> None:
        if not getattr(fn, "_axon_tool", False):
            raise ValueError(f"{fn.__name__} must be decorated with @tool")
        self._tools[fn._axon_tool_spec["name"]] = fn

    def register_all(self, *fns: Callable) -> None:
        for fn in fns:
            self.register(fn)

    def specs(self) -> list[dict]:
        return [fn._axon_tool_spec for fn in self._tools.values()]

    def call(self, name: str, inputs: dict[str, Any]) -> Any:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name](**inputs)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)
