"""Shared MCP path alias resolution for operator dispatch."""

from __future__ import annotations

from typing import Any


def resolve_path_alias(
    alias: str,
    pattern: tuple[str, ...] | None,
    *,
    params: dict[str, Any] | None = None,
) -> tuple[str, ...] | None:
    """Resolve an alias pattern to a concrete command path, substituting ``params`` tokens."""
    if pattern is None:
        return None
    params = params or {}
    resolved: list[str] = []
    for segment in pattern:
        text = str(segment)
        if text.startswith("{") and text.endswith("}"):
            key = text[1:-1]
            value = params.get(key)
            if value is None:
                raise ValueError(f"alias {alias!r} requires param {key!r}")
            resolved.append(str(value))
        else:
            resolved.append(text)
    return tuple(resolved)


__all__ = ["resolve_path_alias"]