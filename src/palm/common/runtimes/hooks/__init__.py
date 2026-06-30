"""Runtime middleware hooks for orchestration jobs."""

from palm.common.runtimes.hooks.child_completion import ChildCompletionHook
from palm.common.runtimes.hooks.execution_context import JobExecutionContextHook
from palm.common.runtimes.hooks.middleware import (
    AuthMiddleware,
    DriveObservabilityHook,
    DriveSlice,
    authenticate_runtime,
)

__all__ = [
    "AuthMiddleware",
    "ChildCompletionHook",
    "DriveObservabilityHook",
    "DriveSlice",
    "JobExecutionContextHook",
    "authenticate_runtime",
]
