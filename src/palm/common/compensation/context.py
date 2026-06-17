"""
Compensation context and result types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CompensationContext:
    """Payload passed to compensation handlers after a triggering event."""

    trigger_event: str
    payload: dict[str, Any]
    hook_name: str | None = None
    resource_ref: str | None = None
    wizard_name: str | None = None
    error: str | None = None
    instance_id: str | None = None
    job_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CompensationResult:
    """Outcome of a compensation handler invocation."""

    ok: bool
    data: Any = None
    error: str | None = None

    @staticmethod
    def success(data: Any = None) -> CompensationResult:
        return CompensationResult(ok=True, data=data)

    @staticmethod
    def failure(message: str) -> CompensationResult:
        return CompensationResult(ok=False, error=message)
