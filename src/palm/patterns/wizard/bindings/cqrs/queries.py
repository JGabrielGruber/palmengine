"""Wizard CQRS query types."""

from __future__ import annotations

from dataclasses import dataclass

from palm.common.cqrs.query import Query


@dataclass(frozen=True)
class GetWizardProgressQuery(Query):
    instance_id: str | None = None
    job_id: str | None = None


@dataclass(frozen=True)
class GetWizardStatusQuery(Query):
    """Rich wizard view keyed by durable instance id."""

    instance_id: str


@dataclass(frozen=True)
class ListWizardProgressQuery(Query):
    """List wizard progress read models (newest first)."""

    limit: int | None = 10
    active_only: bool = False


__all__ = [
    "GetWizardProgressQuery",
    "GetWizardStatusQuery",
    "ListWizardProgressQuery",
]