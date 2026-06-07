"""
Definition reference resolution — shared by library and CLI callers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.exceptions import DefinitionNotFoundError
from palm.definitions.flow import FlowDefinition
from palm.definitions.process import ProcessDefinition

if TYPE_CHECKING:
    from palm.app.app import PalmApp
    from palm.common.persistence.definition_repository import DefinitionRepository


def resolve_flow(repository: DefinitionRepository, ref: str) -> FlowDefinition:
    """Resolve a flow by display name, falling back to definition id."""
    try:
        return repository.get_flow(ref)
    except DefinitionNotFoundError:
        return repository.get_flow(ref, by_id=True)


def resolve_process(repository: DefinitionRepository, ref: str) -> ProcessDefinition:
    """Resolve a process by display name, falling back to definition id."""
    try:
        return repository.get_process(ref)
    except DefinitionNotFoundError:
        return repository.get_process(ref, by_id=True)


def resolve_flow_for_app(app: PalmApp, ref: str, *, runtime_name: str | None = None) -> FlowDefinition:
    """Resolve a flow via a :class:`~palm.app.app.PalmApp` runtime repository."""
    return resolve_flow(app.repository(runtime_name=runtime_name), ref)


def resolve_process_for_app(
    app: PalmApp, ref: str, *, runtime_name: str | None = None
) -> ProcessDefinition:
    """Resolve a process via a :class:`~palm.app.app.PalmApp` runtime repository."""
    return resolve_process(app.repository(runtime_name=runtime_name), ref)