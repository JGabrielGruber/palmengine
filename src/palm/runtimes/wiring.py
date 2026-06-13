"""Backward-compatible re-export — prefer ``palm.common.runtimes.wiring``."""

from palm.common.runtimes.wiring import SchedulerPolicy, resolve_runner, resolve_scheduler

__all__ = ["SchedulerPolicy", "resolve_runner", "resolve_scheduler"]
