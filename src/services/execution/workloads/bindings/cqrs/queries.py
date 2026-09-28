"""Workload CQRS queries (transport only)."""

from __future__ import annotations

from dataclasses import dataclass

from palm.common.cqrs.query import Query


@dataclass(frozen=True)
class GetWorkloadQuery(Query):
    workload_id: str
    refresh: bool = False
    runtime_name: str | None = None


@dataclass(frozen=True)
class ListWorkloadsQuery(Query):
    job_id: str | None = None
    instance_id: str | None = None
    session_id: str | None = None
    status: str | None = None
    runtime: str | None = None
    runtime_name: str | None = None


@dataclass(frozen=True)
class ListWorkloadHostsQuery(Query):
    runtime_name: str | None = None


@dataclass(frozen=True)
class ListWorkloadRuntimesQuery(Query):
    runtime_name: str | None = None


__all__ = [
    "GetWorkloadQuery",
    "ListWorkloadHostsQuery",
    "ListWorkloadRuntimesQuery",
    "ListWorkloadsQuery",
]
