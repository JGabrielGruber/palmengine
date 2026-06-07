"""
Execution runtimes — surfaces that host Palm engines.

- ``embedded`` — in-process library runtime
- ``daemon`` — long-lived background host
- ``cli`` — command-line interface (entry point)
- ``server`` — network host (future)
"""

from palm.runtimes.cli import main
from palm.runtimes.daemon import DaemonRuntime, run_daemon
from palm.runtimes.embedded import EmbeddedRuntime
from palm.runtimes.host import RuntimeHost
from palm.runtimes.hooks import AuthMiddleware, DriveObservabilityHook, DriveSlice
from palm.runtimes.server import ServerRuntime, run_server

__all__ = [
    "AuthMiddleware",
    "DaemonRuntime",
    "DriveObservabilityHook",
    "DriveSlice",
    "EmbeddedRuntime",
    "RuntimeHost",
    "ServerRuntime",
    "main",
    "run_daemon",
    "run_server",
]
