"""
Execution backends — pluggable strategies for advancing Job executables.

Only the abstract `ExecutionBackend` and the pure `TestBackend` (for testing
and the default `TestMode`) live inside `palm/core/orchestration/`.

All other concrete backends live outside core (see `palm/backends/`).
"""

from __future__ import annotations

from .backend import ExecutionBackend
from .test_backend import TestBackend

__all__ = ["ExecutionBackend", "TestBackend"]
