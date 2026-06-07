"""
Palm application layer — configuration, bootstrap, and multi-runtime orchestration.

Use :class:`~palm.app.app.PalmApp` as the top-level entrypoint when embedding
Palm in services, tests, or multi-process deployments.
"""

from palm.app.app import PalmApp
from palm.app.registry import RuntimeHandle, RuntimeKind, RuntimeRegistry
from palm.app.settings import PalmSettings

__all__ = [
    "PalmApp",
    "PalmSettings",
    "RuntimeHandle",
    "RuntimeKind",
    "RuntimeRegistry",
]