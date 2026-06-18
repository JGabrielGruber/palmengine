"""
Abstract behavior-tree pattern contract.

Tree nodes inherit ``BasePattern`` via ``BaseNode``. Domain patterns in
``palm.patterns`` may also implement this contract directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum

from palm.core.context import BaseState


class PatternStatus(StrEnum):
    """Outcome of a single pattern or node tick."""

    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"
    WAITING_FOR_INPUT = "waiting_for_input"
    WAITING_FOR_CHILD = "waiting_for_child"


def is_yielding_status(status: PatternStatus) -> bool:
    """Return whether a tick should pause the parent sequence without failing."""
    return status in (
        PatternStatus.RUNNING,
        PatternStatus.WAITING_FOR_INPUT,
        PatternStatus.WAITING_FOR_CHILD,
    )


# Alias used by migrated behavior-tree nodes
NodeStatus = PatternStatus


class BasePattern(ABC):
    """Abstract node or subtree executed by the behavior tree engine."""

    def __init__(self, *, name: str) -> None:
        if not name:
            raise ValueError("Pattern name must be a non-empty string")
        self.name = name

    @abstractmethod
    def tick(self, state: BaseState) -> PatternStatus:
        """Advance one execution step using shared execution state."""
