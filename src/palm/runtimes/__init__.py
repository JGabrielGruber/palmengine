"""
Execution runtimes — surfaces that host Palm engines.

Use ``palm.runtimes.cli:main`` as the CLI entry point. Library code should
import concrete runtimes from their subpackages (``embedded``, ``daemon``, ``server``).
Shared wiring lives in ``palm.common.runtimes``.
"""

from palm.common.runtimes import (
    AuthMiddleware,
    BaseRuntime,
    DriveObservabilityHook,
    DriveSlice,
    RuntimeHost,
)
from palm.runtimes.daemon import DaemonRuntime, run_daemon
from palm.runtimes.embedded import EmbeddedRuntime
from palm.runtimes.server import ServerRuntime, run_server

__all__ = [
    "AuthMiddleware",
    "BaseRuntime",
    "DaemonRuntime",
    "DriveObservabilityHook",
    "DriveSlice",
    "EmbeddedRuntime",
    "RuntimeHost",
    "ServerRuntime",
    "run_daemon",
    "run_server",
]
