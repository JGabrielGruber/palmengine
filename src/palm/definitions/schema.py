"""
State schema definition — declarative validation contract for flow state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from palm.core.context import DictStateSchema, StateSchema

_DEFINITION_VERSION = 1


@dataclass
class StateSchemaDefinition:
    """Named, versioned schema document for execution state validation."""

    name: str
    schema: dict[str, Any]
    id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("StateSchemaDefinition name must be non-empty")
        if not isinstance(self.schema, dict):
            raise ValueError("StateSchemaDefinition schema must be a dict")

    @property
    def definition_id(self) -> str:
        """Stable identifier used for storage keys (defaults to ``name``)."""
        return self.id if self.id else self.name

    def to_state_schema(self) -> StateSchema:
        """Materialize a core :class:`~palm.core.context.StateSchema` instance."""
        return DictStateSchema(self.schema)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-friendly dict for persistence."""
        payload: dict[str, Any] = {
            "version": _DEFINITION_VERSION,
            "kind": "state_schema",
            "name": self.name,
            "schema": dict(self.schema),
            "metadata": dict(self.metadata),
        }
        if self.id is not None:
            payload["id"] = self.id
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StateSchemaDefinition:
        """Restore a schema definition from ``to_dict`` output or legacy shape."""
        if data.get("kind") == "state_schema" and "version" in data:
            return cls(
                name=str(data["name"]),
                schema=dict(data.get("schema") or {}),
                id=data.get("id"),
                metadata=dict(data.get("metadata") or {}),
            )
        return cls(
            name=str(data["name"]),
            schema=dict(data.get("schema") or {}),
            id=data.get("id"),
            metadata=dict(data.get("metadata") or {}),
        )

    def to_storage_record(self) -> dict[str, Any]:
        """Envelope stored under the repository storage key."""
        return self.to_dict()