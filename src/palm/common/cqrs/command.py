"""
Command types — write-side intent objects dispatched through the host.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class Command:
    """Base marker for host write operations."""


@dataclass(frozen=True)
class SubmitFlowCommand(Command):
    flow: Any
    runtime_name: str | None = None
    by_id: bool = False
    job_id: str | None = None
    state: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SubmitProcessCommand(Command):
    process: Any
    runtime_name: str | None = None
    by_id: bool = False
    job_id: str | None = None
    state: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProvideInputCommand(Command):
    job_id: str
    value: Any
    runtime_name: str | None = None


@dataclass(frozen=True)
class ResumeProcessCommand(Command):
    instance_id: str
    runtime_name: str | None = None


@dataclass(frozen=True)
class PreparePlansCommand(Command):
    """Stage prepared execution plans for deferred submission."""

    body: dict[str, Any]
    runtime_name: str | None = None


@dataclass(frozen=True)
class SubmitPlansCommand(Command):
    """Consume staged plans and submit them to orchestration."""

    plan_ids: list[str]
    runtime_name: str | None = None


@runtime_checkable
class CommandHandler(Protocol):
    """Handle a single command type."""

    def handle(self, command: Command) -> Any:
        """Execute the command and return a result."""



