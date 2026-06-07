"""
Backward-compatibility shim — prefer ``palm.patterns.wizard.handler``.
"""

from __future__ import annotations

from palm.patterns.wizard.handler import (
    CommitContext,
    CommitHandler,
    CommitRegistry,
    CommitResult,
    default_commit_registry,
)

__all__ = [
    "CommitContext",
    "CommitHandler",
    "CommitRegistry",
    "CommitResult",
    "default_commit_registry",
]