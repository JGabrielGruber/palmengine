"""
Palm application layer — configuration, bootstrap, and multi-runtime orchestration.

Use :class:`~palm.app.app.PalmApp` as the top-level entrypoint when embedding
Palm in services, tests, or multi-process deployments.
"""

from palm.app.app import CLI_RUNTIME_NAME, PalmApp
from palm.app.registry import RuntimeHandle, RuntimeKind, RuntimeRegistry
from palm.app.session import create_cli_app, create_console
from palm.app.settings import PalmSettings

__all__ = [
    "CLI_RUNTIME_NAME",
    "PalmApp",
    "PalmSettings",
    "RuntimeHandle",
    "RuntimeKind",
    "RuntimeRegistry",
    "create_cli_app",
    "create_console",
]
