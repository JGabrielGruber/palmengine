"""Project CqrsSchemaRegistry command schemas onto REST request bodies."""

from __future__ import annotations

from typing import Any

from palm.common.cqrs.schemas import CqrsSchemaRegistry
from palm.core.context.state_schema import DictStateSchema


def body_schema_for_command(
    registry: CqrsSchemaRegistry,
    command_type: type,
    *,
    properties: tuple[str, ...] | None = None,
) -> DictStateSchema:
    """Return a DictStateSchema for HTTP JSON bodies derived from a CQRS command schema."""
    base = registry.schema_for(command_type)
    if base is None:
        raise KeyError(f"No schema registered for {command_type!r}")
    definition: dict[str, Any] = dict(base.definition)
    props = dict(definition.get("properties") or {})
    if properties is not None:
        props = {key: props[key] for key in properties if key in props}
    required = [key for key in (definition.get("required") or []) if key in props]
    return DictStateSchema(
        {
            "type": "object",
            "properties": props,
            "required": required,
        }
    )


__all__ = ["body_schema_for_command"]