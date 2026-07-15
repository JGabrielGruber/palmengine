"""
Resource preflight probe registry.

Domains contribute a named preflight probe (``(repository) -> dict``) instead of
``common`` reaching up into a service to compute domain-specific health. The
analytics probe registers here on package import; ``build_resource_preflight``
drains the registry. Mirrors the CQRS / pattern contributor pattern.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

ProbeFn = Callable[[Any], dict[str, Any]]

_lock = threading.RLock()
_probes: dict[str, ProbeFn] = {}


def register_resource_preflight_probe(name: str, probe: ProbeFn) -> None:
    """Register a named preflight probe (thread-safe, idempotent per name)."""
    with _lock:
        _probes[name] = probe


def iter_resource_preflight_probes() -> tuple[tuple[str, ProbeFn], ...]:
    with _lock:
        return tuple(_probes.items())


def clear_resource_preflight_probes() -> None:
    """Remove registered probes (primarily for tests)."""
    with _lock:
        _probes.clear()


__all__ = [
    "ProbeFn",
    "clear_resource_preflight_probes",
    "iter_resource_preflight_probes",
    "register_resource_preflight_probe",
]
