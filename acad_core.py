"""Shared tool registry and JSON-schema helpers for autocad-mcp."""
from __future__ import annotations

import inspect
import typing

# Every @tool-decorated function registers itself here; the MCP layer
# (server.py) reads this dict to answer tools/list and tools/call.
TOOLS: dict = {}


def _json_type(annotation):
    if annotation is inspect._empty or annotation is None:
        return {}
    origin = typing.get_origin(annotation)
    if origin in (list, tuple):
        return {"type": "array", "items": {"type": "number"}}
    if annotation is str:
        return {"type": "string"}
    if annotation is bool:
        return {"type": "boolean"}
    if annotation is int:
        return {"type": "integer"}
    if annotation is float:
        return {"type": "number"}
    return {"type": "string"}


def _build_schema(fn) -> dict:
    try:
        hints = typing.get_type_hints(fn)
    except Exception:  # noqa: BLE001
        hints = {}
    sig = inspect.signature(fn)
    props, required = {}, []
    for name, p in sig.parameters.items():
        if name == "self":
            continue
        props[name] = _json_type(hints.get(name))
        if p.default is inspect._empty:
            required.append(name)
    schema = {"type": "object", "properties": props}
    if required:
        schema["required"] = required
    return schema


def tool(name: str, description: str):
    def deco(fn):
        TOOLS[name] = {
            "fn": fn,
            "name": name,
            "description": inspect.cleandoc(description),
            "inputSchema": _build_schema(fn),
        }
        return fn

    return deco
