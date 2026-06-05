"""
Dynamic registry for patterns, providers, and storage backends.

Registries live in core so engines can resolve implementations by name without
importing concrete classes. Registration of implementations happens outside core.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from palm.core.exceptions import RegistryError

if TYPE_CHECKING:
    from palm.core.behavior_tree.base_pattern import BasePattern
    from palm.core.resource.base_provider import BaseProvider
    from palm.core.storage.base_backend import BaseBackend

T = TypeVar("T")


class Registry(Generic[T]):
    """
    Thread-safe-style name → implementation map for extensible Palm components.

    Parameters
    ----------
    label:
        Human-readable category used in error messages (e.g. ``"pattern"``).
    """

    def __init__(self, label: str) -> None:
        self._label = label
        self._entries: dict[str, type[T]] = {}

    def register(self, name: str, implementation: type[T]) -> None:
        """Register an implementation under ``name``. Overwrites on duplicate."""
        self._entries[name] = implementation

    def get(self, name: str) -> type[T]:
        """Return the implementation class registered under ``name``."""
        try:
            return self._entries[name]
        except KeyError as exc:
            raise RegistryError(
                f"Unknown {self._label} {name!r}. " f"Available: {sorted(self._entries)}"
            ) from exc

    def names(self) -> list[str]:
        """Return sorted registered names."""
        return sorted(self._entries)

    def clear(self) -> None:
        """Remove all registrations (primarily for tests)."""
        self._entries.clear()


pattern_registry: Registry[BasePattern] = Registry("pattern")
provider_registry: Registry[BaseProvider] = Registry("provider")
storage_registry: Registry[BaseBackend] = Registry("storage backend")
