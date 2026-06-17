"""
Event context — correlation metadata propagated with domain events.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EventContext:
    """Cross-cutting identifiers attached to published events."""

    job_id: str | None = None
    instance_id: str | None = None
    trace_id: str | None = None
    principal_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def merged(self, other: EventContext | None) -> EventContext:
        """Combine with ``other``, preferring non-empty values from ``other``."""
        if other is None:
            return self
        return EventContext(
            job_id=other.job_id or self.job_id,
            instance_id=other.instance_id or self.instance_id,
            trace_id=other.trace_id or self.trace_id,
            principal_id=other.principal_id or self.principal_id,
            extra={**self.extra, **other.extra},
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.job_id is not None:
            data["job_id"] = self.job_id
        if self.instance_id is not None:
            data["instance_id"] = self.instance_id
        if self.trace_id is not None:
            data["trace_id"] = self.trace_id
        if self.principal_id is not None:
            data["principal_id"] = self.principal_id
        if self.extra:
            data.update(self.extra)
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> EventContext | None:
        if not data:
            return None
        extra = dict(data)
        job_id = extra.pop("job_id", None)
        instance_id = extra.pop("instance_id", None)
        trace_id = extra.pop("trace_id", None)
        principal_id = extra.pop("principal_id", extra.pop("principal", None))
        return cls(
            job_id=str(job_id) if job_id is not None else None,
            instance_id=str(instance_id) if instance_id is not None else None,
            trace_id=str(trace_id) if trace_id is not None else None,
            principal_id=str(principal_id) if principal_id is not None else None,
            extra=extra,
        )

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> EventContext:
        return cls.from_dict(data) or cls()
