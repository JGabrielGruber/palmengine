"""Open set of registries owned by one system instance.

The set is empty until the caller installs a :class:`~palm.core.registry.Registry`.
``start`` freezes the set and each installed registry before the boot walk.
This module imports nothing from drivers, plugins, bundles, services, or a loader.
"""

from __future__ import annotations

import threading
from typing import Any

from palm.core.registry import Registry


class SystemRegistries:
    """Named registries for one system instance.

    A new kind of table is a new name. The set does not grow a field per kind.
    """

    def __init__(self) -> None:
        self._tables: dict[str, Registry[Any]] = {}
        self._frozen = False
        self._lock = threading.RLock()

    def install(self, name: str, registry: Registry[Any]) -> None:
        """Hold ``registry`` under ``name``. The caller keeps the same object."""
        if not name:
            raise RuntimeError("system registry name is empty")
        if not isinstance(registry, Registry):
            raise RuntimeError(f"system registry {name!r} is not a Registry")
        with self._lock:
            if self._frozen:
                raise RuntimeError(f"system registries are fixed; refused {name!r}")
            if name in self._tables:
                raise RuntimeError(f"system registry {name!r} is already installed")
            self._tables[name] = registry

    def require(self, name: str) -> Registry[Any]:
        """Return the registry installed under ``name``."""
        with self._lock:
            try:
                return self._tables[name]
            except KeyError as exc:
                raise RuntimeError(f"system has no {name} registry") from exc

    def names(self) -> tuple[str, ...]:
        """Return installed registry names in sorted order."""
        with self._lock:
            return tuple(sorted(self._tables))

    def freeze(self) -> None:
        """Refuse further install, and freeze each installed registry."""
        with self._lock:
            if self._frozen:
                return
            self._frozen = True
            installed = tuple(self._tables.values())
        for registry in installed:
            registry.freeze()

    @property
    def frozen(self) -> bool:
        with self._lock:
            return self._frozen


__all__ = ["SystemRegistries"]
