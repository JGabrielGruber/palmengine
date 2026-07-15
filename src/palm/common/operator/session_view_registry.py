"""
Session-view enricher registry.

Surfaces in ``common`` shape a flow session view; domains (assist, …) may blend
their own CTAs onto it. Rather than ``common`` importing a service up to do so,
domains register an enricher here and ``shape_flow_session_view`` drains them.
Mirrors the CQRS / preflight contributor pattern.

An enricher takes the payload plus session metadata and returns a (possibly)
augmented payload::

    enrich(payload, *, session_id, scenario_id, handoff_ready, status) -> dict
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any

EnricherFn = Callable[..., dict[str, Any]]

_lock = threading.RLock()
_enrichers: list[EnricherFn] = []


def register_session_view_enricher(enricher: EnricherFn) -> None:
    """Register a session-view enricher (thread-safe, idempotent per identity)."""
    with _lock:
        if enricher not in _enrichers:
            _enrichers.append(enricher)


def iter_session_view_enrichers() -> tuple[EnricherFn, ...]:
    with _lock:
        return tuple(_enrichers)


def clear_session_view_enrichers() -> None:
    """Remove registered enrichers (primarily for tests)."""
    with _lock:
        _enrichers.clear()


__all__ = [
    "EnricherFn",
    "clear_session_view_enrichers",
    "iter_session_view_enrichers",
    "register_session_view_enricher",
]
