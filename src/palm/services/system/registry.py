"""System service contract — observe/debug verbs (transport-agnostic)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ObserveOperation = Literal[
    "doctor",
    "list_jobs",
    "get_job",
    "inspect_job",
    "list_instances",
    "inspect_instance",
    "list_snapshots",
    "cancel_job",
]


@dataclass(frozen=True)
class ObserveVerb:
    """Declarative observe operation owned by the system domain."""

    verb_id: str
    operation: ObserveOperation
    summary: str = ""


_registry: list[ObserveVerb] = [
    ObserveVerb("doctor", "doctor", "Engine health report"),
    ObserveVerb("list_jobs", "list_jobs", "List orchestration jobs"),
    ObserveVerb("get_job", "get_job", "Get job status"),
    ObserveVerb("inspect_job", "inspect_job", "Inspect job context"),
    ObserveVerb("list_instances", "list_instances", "List durable instances"),
    ObserveVerb("inspect_instance", "inspect_instance", "Pattern-aware instance inspect"),
    ObserveVerb("list_snapshots", "list_snapshots", "List instance snapshots"),
    ObserveVerb("cancel_job", "cancel_job", "Cancel a job"),
]


def observe_verbs() -> tuple[ObserveVerb, ...]:
    return tuple(_registry)


__all__ = ["ObserveOperation", "ObserveVerb", "observe_verbs"]