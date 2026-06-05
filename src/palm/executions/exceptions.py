"""
Execution-layer exceptions (outside core).
"""

from __future__ import annotations


class ExecutionError(Exception):
    """Base error for definition-driven execution."""


class DefinitionBuildError(ExecutionError):
    """Raised when a flow or process definition cannot be built."""


class DefinitionNotFoundError(ExecutionError):
    """Raised when a definition name or id cannot be resolved."""

    def __init__(self, kind: str, ref: str) -> None:
        super().__init__(f"{kind} definition not found: {ref!r}")
        self.kind = kind
        self.ref = ref