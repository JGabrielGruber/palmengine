"""General-purpose recursion guard — depth limits and cycle detection."""

from __future__ import annotations

import contextvars
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

_DEFAULT_MAX_DEPTH = 8

_depth: contextvars.ContextVar[int] = contextvars.ContextVar("palm_recursion_depth", default=0)
_chain: contextvars.ContextVar[tuple[str, ...]] = contextvars.ContextVar(
    "palm_recursion_chain",
    default=(),
)


@dataclass(frozen=True)
class RecursionLimits:
    """Configurable depth limit for nested invocations."""

    max_depth: int = _DEFAULT_MAX_DEPTH


class RecursionGuardError(RuntimeError):
    """Raised when recursion depth or cycle limits are exceeded."""


def chain_key(*parts: str) -> str:
    """Build a stable chain key from ordered parts (e.g. kind + ref)."""
    return ":".join(str(part) for part in parts if part)


@contextmanager
def recursion_frame(
    key: str,
    *,
    limits: RecursionLimits | None = None,
) -> Iterator[tuple[int, tuple[str, ...]]]:
    """
    Enter a nested invocation frame; enforce depth and simple cycle detection.

    Yields ``(depth, chain)`` where ``depth`` is 1 at the outermost nested call.
    """
    resolved = limits or RecursionLimits()
    parent_chain = _chain.get()
    if key in parent_chain:
        raise RecursionGuardError(f"Cycle detected: {key!r} is already active in {parent_chain}")

    depth = _depth.get() + 1
    if depth > resolved.max_depth:
        raise RecursionGuardError(
            f"Recursion depth {depth} exceeds limit {resolved.max_depth} for {key!r}",
        )

    chain = (*parent_chain, key)
    depth_token = _depth.set(depth)
    chain_token = _chain.set(chain)
    try:
        yield depth, chain
    finally:
        _depth.reset(depth_token)
        _chain.reset(chain_token)


def current_depth() -> int:
    """Return active recursion depth (0 at the root)."""
    return _depth.get()


def current_chain() -> tuple[str, ...]:
    """Return the active invocation chain keys."""
    return _chain.get()
