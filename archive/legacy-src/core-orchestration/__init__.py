"""
Palm Orchestration Engine — general-purpose, reusable job & execution coordinator.

This package implements the second general-purpose engine allowed inside
`palm.core` (alongside the Behavior Tree Engine).

Core concepts:
- `Job` + `JobStatus`: universal unit of work with strict lifecycle.
- `Orchestrator`: central coordinator that owns jobs and an EventBus.
- `OrchestrationMode` (Strategy): pluggable runtime behavior
  (TestMode today, EmbeddedMode / ProcessMode tomorrow).
- `ExecutionBackend` (nested Strategy) + `TestBackend`: the only concrete backend allowed inside the core package. All other backends live outside `palm/core/`.
- `Event` + `EventBus` (re-exported from `palm.core.events`): shared observability.

Design invariants (per AGENTS.md):
- Zero knowledge of wizards, CLI, RichContext, persistence, or domain models.
- All data sharing between components goes through Blackboard or the EventBus.
- Fully unit-testable with TestMode + TestBackend (no threads, no I/O).

Public API surface is deliberately small and stable.
"""

from __future__ import annotations

# Re-export the shared core event system (preferred location)
from palm.core.events import Event, EventBus

from .blackboard import Blackboard
from .engine import Orchestrator
from .exceptions import (
    InvalidJobTransitionError,
    JobExecutionError,
    JobNotFoundError,
    ModeError,
    OrchestrationError,
    OrchestratorError,
)
from .execution.backend import ExecutionBackend
from .execution.test_backend import TestBackend
from .job import Job, JobStatus
from .mode.base import OrchestrationMode
from .mode.test_mode import TestMode

__all__ = [
    # Core coordinator
    "Orchestrator",
    # Job model
    "Job",
    "JobStatus",
    # Strategy: modes
    "OrchestrationMode",
    "TestMode",
    # Execution backends (only TestBackend is allowed inside core)
    "ExecutionBackend",
    "TestBackend",
    "Blackboard",  # independent data carrier (no BT dependency)
    # Observability (from core)
    "Event",
    "EventBus",
    # Exceptions
    "OrchestrationError",
    "JobNotFoundError",
    "InvalidJobTransitionError",
    "JobExecutionError",
    "OrchestratorError",
    "ModeError",
]
