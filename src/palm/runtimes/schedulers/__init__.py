"""Backward-compatible re-export — prefer ``palm.common.runtimes.schedulers``."""

from palm.common.runtimes.schedulers import InlineScheduler, QueuedScheduler

__all__ = ["InlineScheduler", "QueuedScheduler"]
