"""
Query types — read-side requests served from projections or fallbacks.
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


@runtime_checkable
class QueryHandler(Protocol):
    """Answer a single query type."""

    def ask(self, query: Query) -> Any:
        """Return the read model result."""