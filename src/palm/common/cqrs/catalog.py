"""CQRS type catalog — single source of truth for host and standalone bus wiring."""

from __future__ import annotations

from typing import Literal

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
from palm.common.cqrs.service_contributors import iter_service_cqrs_contributors
from palm.common.patterns._registry import CqrsContributor
from palm.core.registry import Registry

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


def collect_cqrs_command_types(
    *,
    mode: CatalogMode = "host",
    contributors: Registry[CqrsContributor],
) -> tuple[type, ...]:
    """Return command types for ``mode``.

    The caller passes the pattern table. A name that is not installed is not
    read from the process contributor list. Service command types stay on
    that process list.
    """
    del mode  # command catalog is identical across host and standalone today
    types = _core_command_types()
    for name in contributors.names():
        types.extend(contributors.get(name).command_types)
    for service in iter_service_cqrs_contributors():
        types.extend(service.command_types)
    return tuple(types)


def collect_cqrs_query_types(
    *,
    mode: CatalogMode = "host",
    contributors: Registry[CqrsContributor],
) -> tuple[type, ...]:
    """Return query types for ``mode``.

    The caller passes the pattern table. A name that is not installed is not
    read from the process contributor list. Service query types stay on that
    process list.
    """
    types = _core_query_types(mode=mode)
    for name in contributors.names():
        types.extend(contributors.get(name).query_types)
    for service in iter_service_cqrs_contributors():
        types.extend(service.query_types)
    return tuple(types)


__all__ = [
    "CatalogMode",
    "collect_cqrs_command_types",
    "collect_cqrs_query_types",
]