"""
Execution runtimes — surfaces that host Palm engines.

Import :func:`~palm.runtimes.cli.main` from ``palm.runtimes.cli`` directly to
avoid loading the CLI stack when only library runtimes are needed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.runtimes.daemon import DaemonRuntime, run_daemon
from palm.runtimes.embedded import EmbeddedRuntime
from palm.runtimes.hooks import AuthMiddleware, DriveObservabilityHook, DriveSlice
from palm.runtimes.host import RuntimeHost
from palm.runtimes.server import ServerRuntime, run_server

if TYPE_CHECKING:
    from collections.abc import Callable

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


def __getattr__(name: str) -> Callable[..., int]:
    if name == "main":
        from palm.runtimes.cli import main

        return main
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")