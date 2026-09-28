"""Workload CQRS commands (transport only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from palm.common.cqrs.command import Command


@dataclass(frozen=True)
class StartWorkloadCommand(Command):
    """Allocate and start a workload from a Spec dict."""

    spec: dict[str, Any]
    owner: dict[str, Any] = field(default_factory=dict)
    workload_id: str | None = None
    idempotency_key: str | None = None
    host_id: str | None = None
    runtime_name: str | None = None


@dataclass(frozen=True)
class ExecWorkloadCommand(Command):
    """Run argv on a READY workspace/service."""

    workload_id: str
    command: list[str]
    timeout_s: float | None = None
    env: dict[str, str] = field(default_factory=dict)
    runtime_name: str | None = None


@dataclass(frozen=True)
class StopWorkloadCommand(Command):
    """Idempotent stop."""

    workload_id: str
    runtime_name: str | None = None


@dataclass(frozen=True)
class CancelWorkloadCommand(Command):
    """Owner-driven stop (v1 alias of stop)."""

    workload_id: str
    runtime_name: str | None = None


__all__ = [
    "CancelWorkloadCommand",
    "ExecWorkloadCommand",
    "StartWorkloadCommand",
    "StopWorkloadCommand",
]
