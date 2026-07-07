"""
Flow definition — declarative description of a runnable flow.

Flows reference registered patterns and bind runtime configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from palm.common.persistence.definition_repository import DefinitionRepository
    from palm.core.context import StateSchema

_DEFINITION_VERSION = 1


@dataclass
class FlowDefinition:
    """Named flow with pattern binding, optional metadata, and optional state schema.

    ``state_schema`` (inline dict) or ``state_schema_ref`` (repository lookup) attach
    validation to the execution blackboard. Wizard flows use this for summary/commit
    gates; per-step schemas are configured in wizard step options.
    """

    name: str
    pattern: str
    options: dict[str, Any] = field(default_factory=dict)
    id: str | None = None
    revision: int | None = None
    state_schema_ref: str | None = None
    state_schema: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("FlowDefinition name must be non-empty")
        if not self.pattern:
            raise ValueError("FlowDefinition pattern must be non-empty")

    @property
    def definition_id(self) -> str:
        """Stable identifier used for storage keys (defaults to ``name``)."""
        return self.id if self.id else self.name

    @property
    def has_state_schema(self) -> bool:
        """Return whether inline or referenced state schema is configured."""
        return self.state_schema is not None or self.state_schema_ref is not None

    def materialize_state_schema(
        self,
        repository: DefinitionRepository | None = None,
    ) -> StateSchema | None:
        """Resolve inline schema first, then a repository reference."""
        from palm.common.state.schema_binding import materialize_state_schema

        return materialize_state_schema(
            inline=self.state_schema,
            ref=self.state_schema_ref,
            repository=repository,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-friendly dict for persistence."""
        payload: dict[str, Any] = {
            "version": _DEFINITION_VERSION,
            "kind": "flow",
            "name": self.name,
            "pattern": self.pattern,
            "options": dict(self.options),
        }
        if self.id is not None:
            payload["id"] = self.id
        if self.revision is not None:
            payload["revision"] = self.revision
        if self.state_schema_ref is not None:
            payload["state_schema_ref"] = self.state_schema_ref
        if self.state_schema is not None:
            payload["state_schema"] = dict(self.state_schema)
        return payload

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FlowDefinition:
        """Restore a flow definition from ``to_dict`` output or legacy shape."""
        ref = data.get("state_schema_ref")
        state_schema_ref = str(ref) if ref else None
        inline = data.get("state_schema")
        state_schema = dict(inline) if isinstance(inline, dict) else None
        revision_raw = data.get("revision")
        revision = int(revision_raw) if revision_raw is not None else None
        if data.get("kind") == "flow" and "version" in data:
            return cls(
                name=str(data["name"]),
                pattern=str(data["pattern"]),
                options=dict(data.get("options") or {}),
                id=data.get("id"),
                revision=revision,
                state_schema_ref=state_schema_ref,
                state_schema=state_schema,
            )
        return cls(
            name=str(data["name"]),
            pattern=str(data["pattern"]),
            options=dict(data.get("options") or {}),
            id=data.get("id"),
            revision=revision,
            state_schema_ref=state_schema_ref,
            state_schema=state_schema,
        )

    def catalog_summary(self) -> dict[str, Any]:
        """Minimal catalog list row — facts only, no transport or agent hints."""
        row: dict[str, Any] = {
            "flow_id": self.definition_id,
            "name": self.name,
            "pattern": self.pattern,
            "has_state_schema": self.has_state_schema,
        }
        if self.revision is not None:
            row["revision"] = self.revision
        return row

    def to_storage_record(self) -> dict[str, Any]:
        """Envelope stored under the repository storage key."""
        return self.to_dict()
