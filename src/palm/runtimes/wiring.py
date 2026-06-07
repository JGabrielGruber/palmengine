"""
Runtime wiring — shared scheduler resolution and runner selection.

Keeps concrete runtimes thin: they declare a default scheduling policy and
delegate engine composition to :class:`~palm.runtimes.base.BaseRuntime`.
"""

from __future__ import annotations

import warnings
from typing import Any, Literal

from palm.backends.behavior_tree import BehaviorTreeRunner
from palm.core.orchestration.execution.base_runner import JobRunner
from palm.core.orchestration.mode.base_mode import OrchestrationMode
from palm.runtimes.schedulers import InlineScheduler, QueuedScheduler

SchedulerPolicy = Literal["inline", "queued"]


def resolve_runner(options: dict[str, Any]) -> JobRunner:
    """Select a job runner from startup options."""
    runner = options.get("runner")
    legacy_backend = options.get("backend")
    if runner is None and legacy_backend is not None and not isinstance(legacy_backend, str):
        warnings.warn(
            "backend= as JobRunner is deprecated; use runner= (0.6+)",
            DeprecationWarning,
            stacklevel=3,
        )
        runner = legacy_backend
    return runner if runner is not None else BehaviorTreeRunner()


def resolve_scheduler(
    options: dict[str, Any],
    *,
    default_policy: SchedulerPolicy = "inline",
) -> OrchestrationMode:
    """
    Build or select a scheduler from startup options.

    Accepts an explicit scheduler instance, a policy string (``"inline"`` /
    ``"queued"``), or falls back to ``default_policy`` for the hosting runtime.
    """
    scheduler = options.get("scheduler") or options.get("mode")
    if scheduler is not None and not isinstance(scheduler, str):
        return scheduler

    policy: SchedulerPolicy = default_policy
    if isinstance(scheduler, str):
        policy = _coerce_policy(scheduler)
    elif isinstance(options.get("scheduler_policy"), str):
        policy = _coerce_policy(options["scheduler_policy"])

    runner = resolve_runner(options)
    if policy == "queued":
        return QueuedScheduler(runner=runner)
    return InlineScheduler(runner=runner)


def _coerce_policy(value: str) -> SchedulerPolicy:
    normalized = value.strip().lower()
    if normalized in ("inline", "queued"):
        return normalized  # type: ignore[return-value]
    raise ValueError(f"Unknown scheduler policy {value!r}; expected 'inline' or 'queued'")