"""Recursion guardrails for compositional Palm invocations."""

from __future__ import annotations

import contextvars
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

_DEFAULT_MAX_DEPTH = 8

_depth: contextvars.ContextVar[int] = contextvars.ContextVar("palm_invoke_depth", default=0)
_chain: contextvars.ContextVar[tuple[str, ...]] = contextvars.ContextVar(
    "palm_invoke_chain",
    default=(),
)


@dataclass(frozen=True)
class RecursionLimits:
    """Configurable depth and cycle limits."""

    max_depth: int = _DEFAULT_MAX_DEPTH


class PalmRecursionError(RuntimeError):
    """Raised when recursion depth or cycle limits are exceeded."""


def target_key(kind: str, ref: str) -> str:
    """Stable chain key for cycle detection."""
    return f"{kind}:{ref}"


@contextmanager
def palm_invoke_frame(
    kind: str,
    ref: str,
    *,
    limits: RecursionLimits | None = None,
) -> Iterator[tuple[int, tuple[str, ...]]]:
    """Enter a nested Palm invoke; enforce depth and simple cycle detection."""
    resolved = limits or RecursionLimits()
    key = target_key(kind, ref)
    parent_chain = _chain.get()
    if key in parent_chain:
        raise PalmRecursionError(f"Cycle detected: {key} is already active in {parent_chain}")

    depth = _depth.get() + 1
    if depth > resolved.max_depth:
        raise PalmRecursionError(
            f"Recursion depth {depth} exceeds limit {resolved.max_depth} for {key}",
        )

    chain = parent_chain + (key,)
    depth_token = _depth.set(depth)
    chain_token = _chain.set(chain)
    try:
        yield depth, chain
    finally:
        _depth.reset(depth_token)
        _chain.reset(chain_token)


def current_depth() -> int:
    """Return the active Palm invoke depth (0 at the root)."""
    return _depth.get()


def current_chain() -> tuple[str, ...]:
    """Return the active invocation chain keys."""
    return _chain.get()