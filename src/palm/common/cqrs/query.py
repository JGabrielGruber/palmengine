"""
Query types — read-side requests served from projections or fallbacks.

Add a query dataclass, a handler that reads one or more projections (or
authoritative stores for snapshots), and register both on the host
:class:`~palm.common.cqrs.bus.QueryBus` via :mod:`palm.app.host.cqrs_wiring`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Query:
    """Base marker for host read operations."""


@dataclass(frozen=True)
class ListInstancesQuery(Query):
    status: str | None = None
    flow_name: str | None = None
    include_terminal: bool = True
    limit: int | None = None


@dataclass(frozen=True)
class GetInstanceStatusQuery(Query):
    instance_id: str


@dataclass(frozen=True)
class ListInstanceSnapshotsQuery(Query):
    """Load durable snapshots from authoritative instance storage."""

    instance_id: str


@dataclass(frozen=True)
class GetWizardProgressQuery(Query):
    instance_id: str | None = None
    job_id: str | None = None


@dataclass(frozen=True)
class ListJobStatusQuery(Query):
    status: str | None = None
    limit: int | None = None


@dataclass(frozen=True)
class GetJobStatusQuery(Query):
    job_id: str


@dataclass(frozen=True)
class GetJobContextQuery(Query):
    """Rich job context — pattern state, snapshots, events, and next actions."""

    job_id: str


@dataclass(frozen=True)
class ListWizardProgressQuery(Query):
    """List wizard progress read models (newest first)."""

    limit: int | None = 10
    active_only: bool = False


@dataclass(frozen=True)
class GetResourceInvocationsQuery(Query):
    """Load resource invocation timeline for an instance or job."""

    instance_id: str | None = None
    job_id: str | None = None


@dataclass(frozen=True)
class ListResourceInvocationsQuery(Query):
    """List resource invocation read models (newest first)."""

    limit: int | None = 10


@dataclass(frozen=True)
class GetInstanceSnapshotQuery(Query):
    """Load a single state snapshot by index or ``recorded_at`` timestamp."""

    instance_id: str
    snapshot_id: str


@dataclass(frozen=True)
class ListFlowsQuery(Query):
    """List registered flow definitions from the repository."""

    pattern: str | None = None


@dataclass(frozen=True)
class GetFlowQuery(Query):
    """Load a flow definition by id or name."""

    flow_id: str


@dataclass(frozen=True)
class ListProcessesQuery(Query):
    """List registered process definitions from the repository."""


@dataclass(frozen=True)
class GetProcessQuery(Query):
    """Load a process definition by id or name."""

    process_id: str


@runtime_checkable
class QueryHandler(Protocol):
    """Answer a single query type."""

    def ask(self, query: Query) -> object:
        """Return the read model result."""