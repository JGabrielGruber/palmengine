"""
Pattern app base — Django-style manifest and lifecycle for pattern packages.

Each ``palm.patterns.<name>`` subpackage subclasses :class:`PatternApp` and
registers via :meth:`PatternApp.register` from its ``registry.py``.
"""

from __future__ import annotations

from abc import ABC
from typing import ClassVar


class PatternApp(ABC):
    """Declarative manifest and ``ready()`` hook for a pattern subpackage."""

    name: ClassVar[str]
    label: ClassVar[str] = ""
    palm_layers: ClassVar[tuple[str, ...]] = ()
    depends_on: ClassVar[tuple[str, ...]] = ()
    registry_hooks: ClassVar[tuple[str, ...]] = ()

    def ready(self) -> None:  # noqa: B027 — optional hook like Django AppConfig.ready()
        """Override to register pattern-specific bridges, projections, and CQRS."""

    def register(self) -> None:
        """Register this app and invoke :meth:`ready` once."""
        from palm.patterns._registry import register_pattern_app

        register_pattern_app(self)
        self.ready()


__all__ = ["PatternApp"]