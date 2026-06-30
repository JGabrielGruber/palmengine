"""
Provider extension registry — app manifests and optional lifecycle hooks.

Keeps ``palm.common`` generic; provider-specific logic lives inside each
``palm.providers.<name>`` subpackage and registers hooks at import time.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from palm.common.providers.app import ProviderApp
    from palm.common.runtimes.base import BaseRuntime

RuntimeBindingFn = Callable[["BaseRuntime"], None]
RuntimeUnbindingFn = Callable[[], None]
RuntimeAccessorFn = Callable[[], "BaseRuntime | None"]

_lock = threading.RLock()
_provider_apps: dict[str, Any] = {}
_runtime_binding: RuntimeBindingFn | None = None
_runtime_unbinding: RuntimeUnbindingFn | None = None
_runtime_accessor: RuntimeAccessorFn | None = None


def register_provider_app(app: ProviderApp) -> None:
    """Register a :class:`~palm.common.providers.app.ProviderApp` instance."""
    with _lock:
        name = str(app.name)
        if _provider_apps.get(name) is app:
            return
        _provider_apps[name] = app


def get_provider_app(name: str) -> ProviderApp | None:
    """Return the registered provider app for ``name``, if any."""
    with _lock:
        return _provider_apps.get(name)


def installed_provider_apps() -> list[ProviderApp]:
    """Return provider apps in stable name order."""
    with _lock:
        return [_provider_apps[name] for name in sorted(_provider_apps)]


def register_runtime_binding(
    bind: RuntimeBindingFn,
    *,
    unbind: RuntimeUnbindingFn | None = None,
) -> None:
    """Register in-process runtime attach/detach hooks (palm provider local mode)."""
    with _lock:
        global _runtime_binding, _runtime_unbinding
        _runtime_binding = bind
        if unbind is not None:
            _runtime_unbinding = unbind


def get_runtime_binding() -> RuntimeBindingFn | None:
    """Return the registered runtime binding hook, if any."""
    with _lock:
        return _runtime_binding


def get_runtime_unbinding() -> RuntimeUnbindingFn | None:
    """Return the registered runtime unbinding hook, if any."""
    with _lock:
        return _runtime_unbinding


def register_runtime_accessor(fn: RuntimeAccessorFn) -> None:
    """Register a hook that returns the bound in-process runtime, if any."""
    with _lock:
        global _runtime_accessor
        _runtime_accessor = fn


def get_bound_runtime() -> BaseRuntime | None:
    """Return the bound runtime via the registered accessor hook."""
    with _lock:
        if _runtime_accessor is None:
            return None
        return _runtime_accessor()


def clear_provider_apps() -> None:
    """Remove provider app registrations (primarily for tests)."""
    with _lock:
        _provider_apps.clear()


def clear_runtime_binding() -> None:
    """Remove runtime binding hooks (primarily for tests)."""
    with _lock:
        global _runtime_binding, _runtime_unbinding, _runtime_accessor
        _runtime_binding = None
        _runtime_unbinding = None
        _runtime_accessor = None
