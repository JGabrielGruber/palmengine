"""
Base manager contract for Palm coordination layers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseManager(ABC):
    """Minimal lifecycle surface shared by Palm managers."""

    @abstractmethod
    def initialize(self, **options: Any) -> None:
        """Prepare the manager for use (idempotent)."""

    @abstractmethod
    def shutdown(self) -> None:
        """Release in-memory resources (idempotent)."""

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Whether :meth:`initialize` has completed."""
