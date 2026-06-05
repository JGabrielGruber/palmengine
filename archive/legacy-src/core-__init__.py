"""
Palm Core — pure, general-purpose orchestration primitives only.

As of the 0.3.0-dev clean-core migration, `palm.core` contains **only**
general-purpose, reusable engines:

- Behavior Tree Engine (`palm.core.behavior_tree`)
- Orchestration Engine (`palm.core.orchestration`)
- Shared primitives such as Event + EventBus (`palm.core.events`)

All legacy wizard, orchestration, models, and persistence code has been
relocated to `palm.cli.solid.legacy` as a deprecated reference implementation.

New code inside `palm.core` must never import from `palm.cli.*` or legacy.
"""

from __future__ import annotations

from palm.core.behavior_tree import BehaviorTree, Blackboard, NodeStatus

# Shared observability (used by all engines in core)
from palm.core.events import Event, EventBus

# Orchestration Engine (second general-purpose engine)
from palm.core.orchestration import (
    Blackboard,  # independent data carrier (no BT dep)
    ExecutionBackend,
    Job,
    JobStatus,
    OrchestrationMode,
    Orchestrator,
    TestBackend,
    TestMode,
)

__all__ = [
    # Behavior Tree Engine
    "BehaviorTree",
    "Blackboard",
    "NodeStatus",
    # Shared events
    "Event",
    "EventBus",
    # Orchestration Engine (pure — only TestBackend + independent Blackboard)
    "Orchestrator",
    "Job",
    "JobStatus",
    "OrchestrationMode",
    "TestMode",
    "ExecutionBackend",
    "TestBackend",
    "Blackboard",
]
