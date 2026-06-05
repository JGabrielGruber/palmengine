"""
Shared engine abstractions for the Palm foundational layer.

``BasePalmEngine`` defines the lifecycle contract every core engine implements.
Engines remain pure: they must not import from outside ``palm.core``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BasePalmEngine(ABC):
    """
    Abstract base for all Palm core engines.

    Subclasses own a single responsibility (behavior trees, orchestration,
    storage, etc.) and expose a minimal ``initialize`` / ``shutdown`` lifecycle.
    """

    def __init__(self, *, name: str | None = None) -> None:
        self._name = name or self.__class__.__name__
        self._initialized = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def initialize(self, **options: Any) -> None:
        """Prepare the engine for use. Idempotent after the first call."""
        if self._initialized:
            return
        self._do_initialize(**options)
        self._initialized = True

    def shutdown(self) -> None:
        """Release engine resources. Safe to call multiple times."""
        if not self._initialized:
            return
        self._do_shutdown()
        self._initialized = False

    @abstractmethod
    def _do_initialize(self, **options: Any) -> None:
        """Engine-specific startup hook."""

    @abstractmethod
    def _do_shutdown(self) -> None:
        """Engine-specific teardown hook."""
