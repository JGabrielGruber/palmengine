"""Test helpers for the orchestration event plane (0.45.5)."""

from __future__ import annotations

from typing import Any

from palm.app.host.application_host import ApplicationHost
from palm.core.event import EventEngine


def runtime_event_engine(host: ApplicationHost) -> EventEngine:
    """Return the orchestration bus — where real jobs publish lifecycle events."""
    return host.app.runtime().event


def emit_orchestration_event(host: ApplicationHost, event_type: str, **payload: Any) -> None:
    """Emit on the runtime orchestration bus (not host coordination)."""
    runtime_event_engine(host).emit(event_type, **payload)


__all__ = ["emit_orchestration_event", "runtime_event_engine"]