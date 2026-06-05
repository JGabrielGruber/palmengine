"""
Abstract behavior-tree pattern contract.

Concrete patterns (wizard, DAG, ETL) live in ``palm.patterns`` and register via
``pattern_registry``. Core only defines the execution contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class PatternStatus(Enum):
    """Outcome of a single pattern tick."""

    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"


class BasePattern(ABC):
    """Abstract node or subtree executed by the Behavior Tree engine."""

    def __init__(self, *, name: str) -> None:
        self.name = name

    @abstractmethod
    def tick(self, blackboard: dict[str, Any]) -> PatternStatus:
        """Advance one execution step using shared blackboard state."""
