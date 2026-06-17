"""Resource invocation specs and state placeholder binding."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

_STATE_PLACEHOLDER = re.compile(r"^\{\{\s*state\.([a-zA-Z0-9_.-]+)\s*\}\}$")
_STATE_INLINE = re.compile(r"\{\{\s*state\.([a-zA-Z0-9_.-]+)\s*\}\}")


@dataclass(frozen=True)
class ResolvedResourceSpec:
    """Provider-ready invocation spec resolved from a definition reference."""

    definition_id: str
    name: str
    provider: str
    action: str = "fetch"
    resource_id: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    output_key: str | None = None


def bind_resource_value(value: Any, state: Mapping[str, Any] | Any | None) -> Any:
    """Bind ``{{ state.path }}`` placeholders in strings, dicts, and lists."""
    if state is None:
        return value
    if isinstance(value, str):
        stripped = value.strip()
        match = _STATE_PLACEHOLDER.match(stripped)
        if match:
            return resolve_state_path(state, match.group(1))
        if _STATE_INLINE.search(value):
            return _bind_template_string(value, state)
        return value
    if isinstance(value, dict):
        return {key: bind_resource_value(item, state) for key, item in value.items()}
    if isinstance(value, list):
        return [bind_resource_value(item, state) for item in value]
    return value


def bind_resource_params(
    params: Mapping[str, Any] | None,
    state: Mapping[str, Any] | Any | None,
) -> dict[str, Any]:
    """Return a copy of ``params`` with state placeholders bound."""
    if not params:
        return {}
    return {str(key): bind_resource_value(value, state) for key, value in params.items()}


def bind_resource_id(
    resource_id: str | None,
    params: Mapping[str, Any],
    state: Mapping[str, Any] | Any | None = None,
) -> str | None:
    """Bind ``{{ state.* }}`` and ``{param}`` placeholders in a resource id template."""
    if resource_id is None:
        return None
    text = str(bind_resource_value(resource_id, state))
    for key, value in params.items():
        if value is None:
            continue
        text = text.replace(f"{{{key}}}", str(value))
    return text


def resolve_state_path(state: Mapping[str, Any] | Any, path: str) -> Any:
    """Read a dotted path from a mapping-like or ``.get``-capable state object."""
    current: Any = state
    for part in path.split("."):
        if current is None:
            return None
        if isinstance(current, Mapping):
            current = current.get(part)
            continue
        getter = getattr(current, "get", None)
        if callable(getter):
            current = getter(part)
            continue
        return None
    return current


def _bind_template_string(template: str, state: Mapping[str, Any] | Any) -> str:
    def replace(match: re.Match[str]) -> str:
        value = resolve_state_path(state, match.group(1))
        return "" if value is None else str(value)

    return _STATE_INLINE.sub(replace, template)
