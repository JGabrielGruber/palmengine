"""Backward-compatible re-export — prefer ``palm.common.runtimes.hooks``."""

from palm.common.runtimes.hooks import (
    AuthMiddleware,
    DriveObservabilityHook,
    DriveSlice,
    authenticate_runtime,
)

__all__ = [
    "AuthMiddleware",
    "DriveObservabilityHook",
    "DriveSlice",
    "authenticate_runtime",
]
