"""
ExecutionBackend — backward-compatible alias for :class:`JobRunner`.
"""

from __future__ import annotations

from palm.core.orchestration.execution.base_runner import JobRunner

# Deprecated name kept for transitional imports (0.6+).
ExecutionBackend = JobRunner

__all__ = ["ExecutionBackend", "JobRunner"]