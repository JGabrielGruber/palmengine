"""Palm provider recursion aliases — delegates to core :mod:`palm.core.utils.recursion`."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from palm.core.utils.recursion import (
    RecursionGuardError,
    RecursionLimits,
    chain_key,
    current_chain,
    current_depth,
    recursion_frame,
)

PalmRecursionError = RecursionGuardError


def target_key(kind: str, ref: str) -> str:
    """Stable chain key for Palm compositional targets."""
    return chain_key(kind, ref)


@contextmanager
def palm_invoke_frame(
    kind: str,
    ref: str,
    *,
    limits: RecursionLimits | None = None,
) -> Iterator[tuple[int, tuple[str, ...]]]:
    """Enter a nested Palm invoke using the shared recursion guard."""
    with recursion_frame(target_key(kind, ref), limits=limits) as frame:
        yield frame


__all__ = [
    "PalmRecursionError",
    "RecursionLimits",
    "current_chain",
    "current_depth",
    "palm_invoke_frame",
    "target_key",
]