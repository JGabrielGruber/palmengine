"""
Resource engine — coordinates external data providers.

Resolves providers by name from ``provider_registry``. Core stays free of
concrete HTTP or database implementations.
"""

from __future__ import annotations

from typing import Any

from palm.core.base import BasePalmEngine
from palm.core.registry import provider_registry
from palm.core.resource.base_provider import BaseProvider


class ResourceEngine(BasePalmEngine):
    """Manages lifecycle and lookup of registered resource providers."""

    def __init__(self) -> None:
        super().__init__(name="resource")
        self._active: dict[str, BaseProvider] = {}

    def use(self, name: str) -> BaseProvider:
        """Return a connected provider instance for ``name``."""
        if name not in self._active:
            cls = provider_registry.get(name)
            provider = cls(name=name)
            provider.connect()
            self._active[name] = provider
        return self._active[name]

    def _do_initialize(self, **options: Any) -> None:
        pass

    def _do_shutdown(self) -> None:
        for provider in self._active.values():
            provider.disconnect()
        self._active.clear()
