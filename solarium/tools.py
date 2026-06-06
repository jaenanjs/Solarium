"""Tool registry and decorator for defining agent tools."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any, get_type_hints

# Attributes stamped onto decorated functions
_AXON_TOOL_ATTR = "_solarium_tool"
_AXON_SPEC_ATTR = "_solarium_tool_spec"


def _python_type_to_json(annotation: Any) -> dict[str, Any]:
    """Map Python type hints to JSON Schema types."""
    if annotation is inspect.Parameter.empty or annotation is type(None):
        return {"type": "string"}
    name = getattr(annotation, "__name__", str(annotation))
    mapping: dict[str, dict[str, str]] = {
        "str": {"type": "string"},
        "int": {"type": "integer"},
        "float": {"type": "number"},
        "bool": {"type": "boolean"},
        "list": {"type": "array"},
        "dict": {"type": "object"},
    }
    return mapping.get(name, {"type": "string"})


def tool(
    func: Callable[..., Any] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
) -> Any:
    """Decorator that marks a function as an Solarium tool.

    Usage:
        @tool
        def my_tool(x: str) -> str: ...

        @tool(name="custom_name", description="Does X")
        def my_tool(x: str) -> str: ...
    """
    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
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

        object.__setattr__(fn, _AXON_TOOL_ATTR, True)
        object.__setattr__(fn, _AXON_SPEC_ATTR, {
            "name": tool_name,
            "description": tool_desc,
            "input_schema": {"type": "object", "properties": properties, "required": required},
        })
        return fn

    if func is not None:
        return decorator(func)
    return decorator


def _get_spec(fn: Callable[..., Any]) -> dict[str, Any]:
    spec: dict[str, Any] | None = getattr(fn, _AXON_SPEC_ATTR, None)
    if spec is None:
        raise ValueError(f"{fn.__name__} has no tool spec")
    return spec


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Callable[..., Any]] = {}

    def register(self, fn: Callable[..., Any]) -> None:
        if not getattr(fn, _AXON_TOOL_ATTR, False):
            raise ValueError(f"{fn.__name__} must be decorated with @tool")
        spec = _get_spec(fn)
        self._tools[spec["name"]] = fn

    def register_all(self, *fns: Callable[..., Any]) -> None:
        for fn in fns:
            self.register(fn)

    def specs(self) -> list[dict[str, Any]]:
        return [_get_spec(fn) for fn in self._tools.values()]

    def call(self, name: str, inputs: dict[str, Any]) -> Any:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name](**inputs)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)
