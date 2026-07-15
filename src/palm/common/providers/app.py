"""
Provider app base — Django-style manifest and lifecycle for provider packages.

Each ``palm.providers.<name>`` subpackage subclasses :class:`ProviderApp` and
registers via :meth:`ProviderApp.register` from its ``registry.py``.
"""

from __future__ import annotations

from abc import ABC
from typing import ClassVar


class ProviderApp(ABC):
    """Declarative manifest and ``ready()`` hook for a provider subpackage."""

    name: ClassVar[str]
    label: ClassVar[str] = ""
    palm_layers: ClassVar[tuple[str, ...]] = ()
    actions: ClassVar[tuple[str, ...]] = ()
    depends_on: ClassVar[tuple[str, ...]] = ()
    registry_hooks: ClassVar[tuple[str, ...]] = ()

    def ready(self) -> None:  # noqa: B027 — optional hook like Django AppConfig.ready()
        """Override to register runtime bindings, compensation, and CQRS hooks."""

    def register(self) -> None:
        """Register this app and invoke :meth:`ready` once."""
        from palm.common.providers._registry import register_provider_app

        register_provider_app(self)
        self.ready()


__all__ = ["ProviderApp"]
