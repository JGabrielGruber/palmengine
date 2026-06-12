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


@dataclass
class PatternBuildContext:
    """Runtime services used when constructing executable patterns."""

    event_engine: EventEngine | None = None
    resource_engine: ResourceEngine | None = None
    commit_registry: Any | None = None
    definition_repository: DefinitionRepository | None = None

    def resolve_state_schema(self, ref: str | None) -> StateSchema | None:
        """Resolve a declarative schema reference into a core ``StateSchema``."""
        if not ref or self.definition_repository is None:
            return None
        from palm.common.exceptions import DefinitionNotFoundError

        try:
            definition = self.definition_repository.get_schema(ref)
        except DefinitionNotFoundError:
            try:
                definition = self.definition_repository.get_schema(ref, by_id=True)
            except DefinitionNotFoundError:
                return None
        return definition.to_state_schema()