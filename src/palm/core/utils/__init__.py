"""Core utilities — pure helpers usable across engines and providers."""

from palm.core.utils.recursion import (
    RecursionGuardError,
    RecursionLimits,
    chain_key,
    current_chain,
    current_depth,
    recursion_frame,
)

__all__ = [
    "RecursionGuardError",
    "RecursionLimits",
    "chain_key",
    "current_chain",
    "current_depth",
    "recursion_frame",
]