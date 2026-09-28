"""Definitions service CQRS handlers — thin transport over persistence primitives."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.command import Command, MigrateInstanceCommand
from palm.common.cqrs.query import AnalyzeDefinitionImpactQuery, Query
from palm.common.persistence.definition_impact import analyze_definition_impact_or_raise
from palm.common.persistence.instance_migration import migrate_instance

if TYPE_CHECKING:
    from palm.common.managers.instance_manager import InstanceManager
    from palm.common.persistence.definition_repository import DefinitionRepository


class DefinitionsCommandHandler:
    """Dispatch definitions write commands."""

    def __init__(
        self,
        *,
        repository: DefinitionRepository,
        instance_manager: InstanceManager,
    ) -> None:
        self._repository = repository
        self._instance_manager = instance_manager

    def handle(self, command: Command) -> Any:
        if isinstance(command, MigrateInstanceCommand):
            return migrate_instance(
                self._repository,
                self._instance_manager,
                instance_id=command.instance_id,
                target_revision=command.target_revision,
                dry_run=command.dry_run,
            )
        raise TypeError(f"Unsupported definitions command: {type(command).__name__}")


class DefinitionsQueryHandler:
    """Dispatch definitions read queries."""

    def __init__(
        self,
        *,
        repository: DefinitionRepository,
        instance_manager: InstanceManager,
    ) -> None:
        self._repository = repository
        self._instance_manager = instance_manager

    def ask(self, query: Query) -> Any:
        if isinstance(query, AnalyzeDefinitionImpactQuery):
            return analyze_definition_impact_or_raise(
                self._repository,
                self._instance_manager.list_instances(),
                flow_id=query.flow_id,
                target_revision=query.target_revision,
            )
        raise TypeError(f"Unsupported definitions query: {type(query).__name__}")


__all__ = ["DefinitionsCommandHandler", "DefinitionsQueryHandler"]