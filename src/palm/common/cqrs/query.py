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


@runtime_checkable
class QueryHandler(Protocol):
    """Answer a single query type."""

    def ask(self, query: Query) -> object:
        """Return the read model result."""