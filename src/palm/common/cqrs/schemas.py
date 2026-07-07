"""
CQRS schema registry — validation and introspection for commands and queries.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any

from palm.core.context.state_schema import DictStateSchema


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of validating a CQRS instance against its registered schema."""

    ok: bool
    errors: list[str]
    details: list[dict[str, str]]


class CqrsSchemaRegistry:
    """Maps command/query types to :class:`DictStateSchema` contracts."""

    def __init__(self) -> None:
        self._commands: dict[type, DictStateSchema] = {}
        self._queries: dict[type, DictStateSchema] = {}

    def register_command(self, command_type: type, schema: DictStateSchema) -> None:
        self._commands[command_type] = schema

    def register_query(self, query_type: type, schema: DictStateSchema) -> None:
        self._queries[query_type] = schema

    def schema_for(self, cqrs_type: type) -> DictStateSchema | None:
        return self._commands.get(cqrs_type) or self._queries.get(cqrs_type)

    def command_types(self) -> tuple[type, ...]:
        return tuple(self._commands)

    def query_types(self) -> tuple[type, ...]:
        return tuple(self._queries)

    def validate(self, instance: Any) -> ValidationResult:
        schema = self.schema_for(type(instance))
        if schema is None:
            return ValidationResult(ok=True, errors=[], details=[])
        payload = _payload_for_validation(instance)
        errors = list(schema.validate_state(payload))
        details = [_error_detail(message) for message in errors]
        return ValidationResult(ok=not errors, errors=errors, details=details)


def build_schema_registry() -> CqrsSchemaRegistry:
    """Build a registry from core schemas and pattern CQRS contributors."""
    import palm.patterns  # noqa: F401 — ensure pattern contributors are registered
    from palm.common.cqrs.schema_bootstrap import register_core_schemas
    from palm.patterns._registry import iter_cqrs_contributors

    registry = CqrsSchemaRegistry()
    register_core_schemas(registry)
    for contributor in iter_cqrs_contributors():
        for command_type, schema in contributor.command_schemas.items():
            registry.register_command(command_type, schema)
        for query_type, schema in contributor.query_schemas.items():
            registry.register_query(query_type, schema)
    from palm.services.design.bindings.cqrs.schemas import register_design_cqrs_schemas

    register_design_cqrs_schemas(registry)
    return registry


def _payload_for_validation(instance: Any) -> dict[str, Any]:
    if is_dataclass(instance):
        return asdict(instance)
    if isinstance(instance, dict):
        return dict(instance)
    raise TypeError(f"Cannot validate CQRS payload for {type(instance).__name__}")


def _error_detail(message: str) -> dict[str, str]:
    if message.startswith("missing required key: "):
        field = message.removeprefix("missing required key: ")
        return {"field": field, "message": "is required"}
    if ": " in message:
        field, text = message.split(": ", 1)
        return {"field": field, "message": text}
    return {"field": "body", "message": message}


__all__ = ["CqrsSchemaRegistry", "ValidationResult", "build_schema_registry"]
