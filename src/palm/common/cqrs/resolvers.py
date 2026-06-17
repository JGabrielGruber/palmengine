"""
CQRS resolvers — shared lookup helpers for authoritative stores.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.exceptions import DefinitionNotFoundError
from palm.common.persistence.definition_repository import DefinitionRepository

if TYPE_CHECKING:
    from palm.definitions.flow import FlowDefinition
    from palm.definitions.process import ProcessDefinition
    from palm.instances import StateSnapshot


def resolve_flow(repository: DefinitionRepository, flow_id: str) -> FlowDefinition:
    """Load a flow by definition id, falling back to display name."""
    try:
        return repository.get_flow(flow_id, by_id=True)
    except DefinitionNotFoundError:
        return repository.get_flow(flow_id, by_id=False)


def resolve_process(repository: DefinitionRepository, process_id: str) -> ProcessDefinition:
    """Load a process by definition id, falling back to display name."""
    try:
        return repository.get_process(process_id, by_id=True)
    except DefinitionNotFoundError:
        return repository.get_process(process_id, by_id=False)


def resolve_snapshot(
    snapshots: list[StateSnapshot],
    snapshot_id: str,
) -> tuple[int, StateSnapshot] | None:
    """
    Find a snapshot by zero-based index (``snapshot_id`` digit) or ``recorded_at``.

    Returns ``(index, snapshot)`` or ``None``.
    """
    if snapshot_id.isdigit():
        index = int(snapshot_id)
        if 0 <= index < len(snapshots):
            return index, snapshots[index]
    for index, snapshot in enumerate(snapshots):
        if snapshot.recorded_at == snapshot_id:
            return index, snapshot
    return None