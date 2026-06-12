"""
Build context — dependencies passed when materializing patterns from definitions.

Pattern-specific defaults (e.g. wizard commit registries) are resolved inside
each ``palm.patterns.<name>`` builder, not here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from palm.core.context import StateSchema
from palm.core.event import EventEngine
from palm.core.resource import ResourceEngine

if TYPE_CHECKING:
    from palm.common.persistence.definition_repository import DefinitionRepository
    from palm.definitions.flow import FlowDefinition


@dataclass
class PatternBuildContext:
    """Runtime services used when constructing executable patterns."""

    event_engine: EventEngine | None = None
    resource_engine: ResourceEngine | None = None
    commit_registry: Any | None = None
    definition_repository: DefinitionRepository | None = None

    def resolve_state_schema(self, ref: str | None) -> StateSchema | None:
        """Resolve a declarative schema reference into a core ``StateSchema``."""
        from palm.common.state.schema_binding import materialize_state_schema

        return materialize_state_schema(ref=ref, repository=self.definition_repository)

    def resolve_flow_state_schema(self, flow: FlowDefinition) -> StateSchema | None:
        """Resolve a flow's inline schema first, then a repository reference."""
        return flow.materialize_state_schema(self.definition_repository)