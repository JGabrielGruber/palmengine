"""
Execution runtimes — surfaces that host Palm engines.

Use ``palm.runtimes.cli:main`` as the CLI entry point. Library code should
import concrete runtimes from their modules directly.
"""

from palm.runtimes.daemon import DaemonRuntime, run_daemon
from palm.runtimes.embedded import EmbeddedRuntime
from palm.runtimes.hooks import AuthMiddleware, DriveObservabilityHook, DriveSlice
from palm.runtimes.host import RuntimeHost
from palm.runtimes.server import ServerRuntime, run_server

__all__ = [
    "AuthMiddleware",
    "DaemonRuntime",
    "DriveObservabilityHook",
    "DriveSlice",
    "EmbeddedRuntime",
    "RuntimeHost",
    "ServerRuntime",
    "run_daemon",
    "run_server",
]