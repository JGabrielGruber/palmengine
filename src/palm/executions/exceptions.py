"""
Execution-layer exceptions (outside core).
"""

from __future__ import annotations


class ExecutionError(Exception):
    """Base error for definition-driven execution."""


class DefinitionBuildError(ExecutionError):
    """Raised when a flow or process definition cannot be built."""