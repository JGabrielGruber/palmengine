"""
Dynamic registry for patterns, providers, and storage backends.

Registries live in core so engines can resolve implementations by name without
importing concrete classes. Registration of implementations happens outside core.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Generic, TypeVar

from palm.core.exceptions import RegistryError

if TYPE_CHECKING:
    from palm.core.behavior_tree.base_pattern import BasePattern
    from palm.core.resource.base_provider import BaseProvider
    from palm.core.storage.base_backend import BaseBackend

T = TypeVar("T")


class Registry(Generic[T]):
    """
    Thread-safe name → implementation map for extensible Palm components.

    Uses a reentrant lock so concurrent readers and bootstrap-time writers
    do not corrupt the map. Re-registering the same ``(name, implementation)``
    pair is a no-op.

    Parameters
    ----------
    label:
        Human-readable category used in error messages (e.g. ``"pattern"``).
    """

    def __init__(self, label: str) -> None:
        self._label = label
        self._entries: dict[str, T] = {}
        self._frozen = False
        self._lock = threading.RLock()

    def register(self, name: str, implementation: T) -> None:
        """Register ``implementation`` under ``name``. The same pair is a no-op."""
        with self._lock:
            if self._entries.get(name) is implementation:
                return
            if self._frozen:
                raise RegistryError(f"{self._label} registry is fixed; refused {name!r}")
            self._entries[name] = implementation

    def get(self, name: str) -> T:
        """Return the implementation registered under ``name``."""
        with self._lock:
            try:
                return self._entries[name]
            except KeyError as exc:
                available = sorted(self._entries)
                raise RegistryError(
                    f"Unknown {self._label} {name!r}. Available: {available}"
                ) from exc

    def names(self) -> list[str]:
        """Return sorted registered names."""
        with self._lock:
            return sorted(self._entries)

    def drop(self, name: str) -> None:
        """Remove one name. A missing name is a no-op."""
        with self._lock:
            if self._frozen:
                raise RegistryError(f"{self._label} registry is fixed; refused drop {name!r}")
            self._entries.pop(name, None)

    def clear(self) -> None:
        """Remove all registrations (primarily for tests)."""
        with self._lock:
            if self._frozen:
                raise RegistryError(f"{self._label} registry is fixed")
            self._entries.clear()

    def freeze(self) -> None:
        """Refuse later register, drop, and clear. Idempotent."""
        with self._lock:
            self._frozen = True

    @property
    def frozen(self) -> bool:
        with self._lock:
            return self._frozen


pattern_registry: Registry[type[BasePattern]] = Registry("pattern")
provider_registry: Registry[type[BaseProvider]] = Registry("provider")
storage_registry: Registry[type[BaseBackend]] = Registry("storage backend")
