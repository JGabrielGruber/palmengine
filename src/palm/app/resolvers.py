"""
Definition reference resolution — shared by library and CLI callers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.exceptions import DefinitionNotFoundError
from palm.definitions.flow import FlowDefinition
from palm.definitions.process import ProcessDefinition
from palm.definitions.resource import ResourceDefinition

if TYPE_CHECKING:
    from palm.app.kernel import PalmKernel
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


def resolve_flow_for_app(
    app: PalmKernel, ref: str, *, runtime_name: str | None = None
) -> FlowDefinition:
    """Resolve a flow via a :class:`~palm.app.kernel.PalmKernel` runtime repository."""
    return resolve_flow(app.repository(runtime_name=runtime_name), ref)


def resolve_process_for_app(
    app: PalmKernel, ref: str, *, runtime_name: str | None = None
) -> ProcessDefinition:
    """Resolve a process via a :class:`~palm.app.kernel.PalmKernel` runtime repository."""
    return resolve_process(app.repository(runtime_name=runtime_name), ref)


def resolve_resource(repository: DefinitionRepository, ref: str) -> ResourceDefinition:
    """Resolve a resource by display name, falling back to definition id."""
    try:
        return repository.get_resource(ref)
    except DefinitionNotFoundError:
        return repository.get_resource(ref, by_id=True)


def resolve_resource_for_app(
    app: PalmKernel, ref: str, *, runtime_name: str | None = None
) -> ResourceDefinition:
    """Resolve a resource via a :class:`~palm.app.kernel.PalmKernel` runtime repository."""
    return resolve_resource(app.repository(runtime_name=runtime_name), ref)
