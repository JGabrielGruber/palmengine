"""
Build context — dependencies passed when materializing patterns from definitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from palm.core.event import EventEngine
from palm.core.resource import ResourceEngine

if TYPE_CHECKING:
    pass


@dataclass
class PatternBuildContext:
    """Runtime services used when constructing executable patterns."""

    event_engine: EventEngine | None = None
    resource_engine: ResourceEngine | None = None
    commit_registry: Any | None = None
    validation_registry: Any | None = None
    wizard_metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def resolved_commit_registry(self) -> Any:
        if self.commit_registry is not None:
            return self.commit_registry
        from palm.patterns.wizard.handler import default_commit_registry

        return default_commit_registry()

    @property
    def resolved_validation_registry(self) -> Any:
        if self.validation_registry is not None:
            return self.validation_registry
        from palm.patterns.wizard.validation import default_validation_registry

        return default_validation_registry()