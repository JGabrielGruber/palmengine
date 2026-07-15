"""CQRS type catalog — single source of truth for host and standalone bus wiring."""

from __future__ import annotations

from typing import Literal

import palm.patterns  # — ensure pattern contributors are registered
import palm.services.definitions.bindings.cqrs.contributor
import palm.services.design.bindings.cqrs.contributor  # noqa: F401
from palm.common.cqrs.command import (
    CancelJobCommand,
    MigrateInstanceCommand,
    PreparePlansCommand,
    ProvideInputCommand,
    ResumeProcessCommand,
    SubmitFlowCommand,
    SubmitPlansCommand,
    SubmitProcessCommand,
)
from palm.common.cqrs.query import (
    AnalyzeDefinitionImpactQuery,
    GetFlowQuery,
    GetInstanceSnapshotQuery,
    GetInstanceStatusQuery,
    GetJobContextQuery,
    GetJobStatusQuery,
    GetProcessQuery,
    GetResourceInvocationsQuery,
    InspectInstanceQuery,
    ListFlowsQuery,
    ListInstanceSnapshotsQuery,
    ListInstancesQuery,
    ListJobStatusQuery,
    ListProcessesQuery,
    ListResourceInvocationsQuery,
)
from palm.patterns._registry import iter_cqrs_contributors
from palm.services._cqrs_registry import iter_service_cqrs_contributors

CatalogMode = Literal["host", "standalone"]

_HOST_ONLY_QUERY_TYPES: tuple[type, ...] = (
    GetResourceInvocationsQuery,
    ListResourceInvocationsQuery,
)


def _core_command_types() -> list[type]:
    return [
        SubmitFlowCommand,
        SubmitProcessCommand,
        ProvideInputCommand,
        ResumeProcessCommand,
        PreparePlansCommand,
        SubmitPlansCommand,
        CancelJobCommand,
        MigrateInstanceCommand,
    ]


def _core_query_types(*, mode: CatalogMode) -> list[type]:
    types: list[type] = [
        ListInstancesQuery,
        GetInstanceStatusQuery,
        ListInstanceSnapshotsQuery,
        GetInstanceSnapshotQuery,
        ListFlowsQuery,
        AnalyzeDefinitionImpactQuery,
        GetFlowQuery,
        ListProcessesQuery,
        GetProcessQuery,
        GetJobStatusQuery,
        GetJobContextQuery,
        InspectInstanceQuery,
        ListJobStatusQuery,
    ]
    if mode == "host":
        types.extend(_HOST_ONLY_QUERY_TYPES)
    return types


def collect_cqrs_command_types(*, mode: CatalogMode = "host") -> tuple[type, ...]:
    """Return all command types registered on the command bus for ``mode``."""
    del mode  # command catalog is identical across host and standalone today
    types = _core_command_types()
    for contributor in iter_cqrs_contributors():
        types.extend(contributor.command_types)
    for contributor in iter_service_cqrs_contributors():
        types.extend(contributor.command_types)
    return tuple(types)


def collect_cqrs_query_types(*, mode: CatalogMode = "host") -> tuple[type, ...]:
    """Return all query types registered on the query bus for ``mode``."""
    types = _core_query_types(mode=mode)
    for contributor in iter_cqrs_contributors():
        types.extend(contributor.query_types)
    for contributor in iter_service_cqrs_contributors():
        types.extend(contributor.query_types)
    return tuple(types)


__all__ = [
    "CatalogMode",
    "collect_cqrs_command_types",
    "collect_cqrs_query_types",
]