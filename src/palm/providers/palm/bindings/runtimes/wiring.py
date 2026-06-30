"""Bind a live runtime for local Palm provider invocations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from palm.common.runtimes.base import BaseRuntime

_bound_runtime: Any | None = None


def bind_palm_runtime(runtime: BaseRuntime) -> None:
    """Attach the active runtime for in-process ``palm`` provider calls."""
    global _bound_runtime
    _bound_runtime = runtime


def get_bound_runtime() -> BaseRuntime | None:
    """Return the runtime bound for local Palm invocations, if any."""
    return _bound_runtime


def clear_palm_runtime() -> None:
    """Clear the bound runtime (tests and shutdown)."""
    global _bound_runtime
    _bound_runtime = None
